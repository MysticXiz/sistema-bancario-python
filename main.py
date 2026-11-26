import sqlite3
from contextlib import asynccontextmanager, closing, contextmanager
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Literal
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, StringConstraints

AGENCIA = "0001"
LIMITE_SAQUE_CENTAVOS = 50_000
LIMITE_TRANSACOES = 10
FUSO = ZoneInfo("America/Sao_Paulo")
CENTAVO = Decimal("0.01")
MAX_INTEIRO_SQLITE = 2**63 - 1
FRONTEND = Path(__file__).with_name("index.html")
BANCO = Path(__file__).with_name("banco.sqlite3")

ESQUEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    cpf TEXT PRIMARY KEY NOT NULL,
    nome TEXT NOT NULL,
    data_nascimento TEXT NOT NULL,
    endereco TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS contas (
    numero INTEGER PRIMARY KEY,
    cpf TEXT NOT NULL REFERENCES usuarios(cpf),
    saldo_centavos INTEGER NOT NULL DEFAULT 0 CHECK (saldo_centavos >= 0)
);
CREATE TABLE IF NOT EXISTS movimentacoes (
    id INTEGER PRIMARY KEY,
    conta INTEGER NOT NULL REFERENCES contas(numero),
    tipo TEXT NOT NULL CHECK (tipo IN ('deposito', 'saque')),
    valor_centavos INTEGER NOT NULL CHECK (valor_centavos > 0),
    realizado_em TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_movimentacoes_conta_data
    ON movimentacoes (conta, realizado_em);
"""

CONSULTA_CONTAS = """
SELECT c.numero, u.nome AS titular, c.saldo_centavos
FROM contas AS c JOIN usuarios AS u ON u.cpf = c.cpf
"""

CPF = Annotated[str, StringConstraints(pattern=r"^[0-9]{11}$")]
Texto = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


class Titular(BaseModel):
    cpf: CPF


class Usuario(Titular):
    nome: Texto
    data_nascimento: date
    endereco: Texto


class Valor(BaseModel):
    valor: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class Movimento(BaseModel):
    tipo: Literal["deposito", "saque"]
    valor: Decimal
    realizado_em: datetime


class Resumo(BaseModel):
    numero: int
    agencia: str
    titular: str
    saldo: Decimal


class Extrato(Resumo):
    movimentacoes: list[Movimento]


def resumo(conta: sqlite3.Row) -> Resumo:
    return Resumo(
        numero=conta["numero"], agencia=AGENCIA, titular=conta["titular"],
        saldo=Decimal(conta["saldo_centavos"]) * CENTAVO,
    )


def buscar_conta(db: sqlite3.Connection, numero: int) -> sqlite3.Row:
    if 0 < numero <= MAX_INTEIRO_SQLITE:
        conta = db.execute(CONSULTA_CONTAS + "WHERE c.numero = ?", (numero,)).fetchone()
        if conta is not None:
            return conta
    raise HTTPException(404, "Conta não encontrada.")


def extrato(db: sqlite3.Connection, conta: sqlite3.Row) -> Extrato:
    linhas = db.execute(
        "SELECT tipo, valor_centavos, realizado_em FROM movimentacoes WHERE conta = ? ORDER BY id",
        (conta["numero"],),
    )
    movimentos = [
        Movimento(tipo=linha["tipo"], valor=Decimal(linha["valor_centavos"]) * CENTAVO,
                  realizado_em=linha["realizado_em"])
        for linha in linhas
    ]
    return Extrato(**resumo(conta).model_dump(), movimentacoes=movimentos)


def criar_app(caminho_banco: Path = BANCO) -> FastAPI:
    @contextmanager
    def conectar(*, escrita: bool = False):
        with closing(sqlite3.connect(caminho_banco)) as db, db:
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA foreign_keys = ON")
            # Reserve a escrita antes de consultar o saldo e o limite diário.
            db.execute("BEGIN IMMEDIATE" if escrita else "BEGIN")
            yield db

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        with closing(sqlite3.connect(caminho_banco)) as db:
            db.executescript(ESQUEMA)
        yield

    app = FastAPI(title="Banco Python", version="1.0.0", lifespan=lifespan)

    def movimentar(numero: int, tipo: Literal["deposito", "saque"], valor: Decimal) -> Extrato:
        centavos = int(valor / CENTAVO)
        with conectar(escrita=True) as db:
            conta = buscar_conta(db, numero)
            agora = datetime.now(FUSO)
            hoje = agora.date()
            amanha = hoje + timedelta(days=1)
            total_hoje = db.execute(
                "SELECT COUNT(*) FROM movimentacoes WHERE conta = ? AND realizado_em >= ? AND realizado_em < ?",
                (numero, hoje.isoformat(), amanha.isoformat()),
            ).fetchone()[0]
            if total_hoje >= LIMITE_TRANSACOES:
                raise HTTPException(409, "Limite de 10 movimentações diárias atingido.")
            saldo = conta["saldo_centavos"]
            if tipo == "saque":
                if centavos > LIMITE_SAQUE_CENTAVOS:
                    raise HTTPException(409, "O limite por saque é de R$ 500,00.")
                if centavos > saldo:
                    raise HTTPException(409, "Saldo insuficiente para realizar o saque.")
                centavos_saldo = saldo - centavos
            else:
                centavos_saldo = saldo + centavos

            db.execute("UPDATE contas SET saldo_centavos = ? WHERE numero = ?", (centavos_saldo, numero))
            db.execute(
                "INSERT INTO movimentacoes (conta, tipo, valor_centavos, realizado_em) VALUES (?, ?, ?, ?)",
                (numero, tipo, centavos, agora.isoformat()),
            )
            return extrato(db, buscar_conta(db, numero))

    @app.get("/", include_in_schema=False)
    async def interface():
        return FileResponse(FRONTEND, media_type="text/html")

    @app.post("/api/usuarios", status_code=201)
    def cadastrar_usuario(usuario: Usuario) -> Titular:
        with conectar(escrita=True) as db:
            insercao = db.execute(
                "INSERT INTO usuarios (cpf, nome, data_nascimento, endereco) VALUES (?, ?, ?, ?) "
                "ON CONFLICT (cpf) DO NOTHING",
                (usuario.cpf, usuario.nome, usuario.data_nascimento.isoformat(), usuario.endereco),
            )
            if not insercao.rowcount:
                raise HTTPException(409, "Já existe um usuário com este CPF.")
        return Titular(cpf=usuario.cpf)

    @app.post("/api/contas", status_code=201)
    def abrir_conta(titular: Titular) -> Resumo:
        with conectar(escrita=True) as db:
            insercao = db.execute(
                "INSERT INTO contas (cpf) SELECT cpf FROM usuarios WHERE cpf = ?", (titular.cpf,),
            )
            if not insercao.rowcount:
                raise HTTPException(404, "Cadastre o usuário antes de abrir a conta.")
            return resumo(buscar_conta(db, insercao.lastrowid))

    @app.get("/api/contas")
    def listar_contas() -> list[Resumo]:
        with conectar() as db:
            return [resumo(conta) for conta in db.execute(CONSULTA_CONTAS + "ORDER BY c.numero")]

    @app.get("/api/contas/{numero}/extrato")
    def consultar_extrato(numero: int) -> Extrato:
        with conectar() as db:
            return extrato(db, buscar_conta(db, numero))

    @app.post("/api/contas/{numero}/depositos", status_code=201)
    def depositar(numero: int, entrada: Valor) -> Extrato:
        return movimentar(numero, "deposito", entrada.valor)

    @app.post("/api/contas/{numero}/saques", status_code=201)
    def sacar(numero: int, entrada: Valor) -> Extrato:
        return movimentar(numero, "saque", entrada.valor)

    return app


app = criar_app()
