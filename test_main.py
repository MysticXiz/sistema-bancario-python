import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import FUSO, criar_app

CLIENTE = {
    "cpf": "00000000000",
    "nome": "Ana Silva",
    "data_nascimento": "1998-05-20",
    "endereco": "Rua Exemplo, 123",
}


class BancoTest(unittest.TestCase):
    def setUp(self):
        pasta = TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        self.banco = Path(pasta.name) / "teste.sqlite3"
        self.sessao = ExitStack()
        self.addCleanup(self.sessao.close)
        self.client = self.sessao.enter_context(TestClient(criar_app(self.banco)))
        self.titular = {"cpf": CLIENTE["cpf"]}

    def abrir_conta(self):
        resposta = self.client.post("/api/contas", json=self.titular)
        self.assertEqual(resposta.status_code, 201)
        return resposta.json()["numero"]

    def movimentar(self, numero, rota, valor):
        return self.client.post(f"/api/contas/{numero}/{rota}", json={"valor": valor})

    def test_interface_e_documentacao(self):
        resposta = self.client.get("/")
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("text/html", resposta.headers["content-type"])
        self.assertIn("Banco Python", resposta.text)
        self.assertEqual(self.client.get("/docs").status_code, 200)

    def test_cadastro_e_contas(self):
        self.assertEqual(self.client.post("/api/contas", json=self.titular).status_code, 404)
        self.assertEqual(self.client.post("/api/usuarios", json=CLIENTE).status_code, 201)
        self.assertEqual(self.client.post("/api/usuarios", json=CLIENTE).status_code, 409)
        self.assertEqual(self.abrir_conta(), 1)
        self.assertEqual(self.client.get("/api/contas").json(), [
            {"numero": 1, "agencia": "0001", "titular": "Ana Silva", "saldo": "0.00"}
        ])
        self.assertEqual(self.client.get("/api/contas/2/extrato").status_code, 404)
        self.assertEqual(self.client.get(f"/api/contas/{2**63}/extrato").status_code, 404)

    def test_valores_e_saldos_independentes(self):
        self.client.post("/api/usuarios", json=CLIENTE)
        primeira, segunda = self.abrir_conta(), self.abrir_conta()
        for invalido in ("0", "-1", "1.001", "NaN", "Infinity"):
            self.assertEqual(self.movimentar(primeira, "depositos", invalido).status_code, 422)
        self.assertEqual(self.movimentar(primeira, "saques", "1").status_code, 409)
        self.assertEqual(self.movimentar(primeira, "depositos", "600.10").status_code, 201)
        self.assertEqual(self.movimentar(primeira, "saques", "500.01").status_code, 409)
        resposta = self.movimentar(primeira, "saques", "500")
        self.assertEqual(resposta.status_code, 201)
        extrato = self.client.get(f"/api/contas/{primeira}/extrato").json()
        self.assertEqual(extrato["saldo"], "100.10")
        self.assertEqual([item["tipo"] for item in extrato["movimentacoes"]], ["deposito", "saque"])
        reserva = self.client.get(f"/api/contas/{segunda}/extrato").json()
        self.assertEqual(reserva["saldo"], "0.00")
        self.assertEqual(reserva["movimentacoes"], [])

    def test_dados_persistem_entre_inicializacoes(self):
        self.assertEqual(self.client.post("/api/usuarios", json=CLIENTE).status_code, 201)
        numero = self.abrir_conta()
        deposito = self.movimentar(numero, "depositos", "12.34")
        self.assertEqual(deposito.status_code, 201)
        self.sessao.close()

        with TestClient(criar_app(self.banco)) as reiniciado:
            self.assertEqual(reiniciado.get(f"/api/contas/{numero}/extrato").json(), deposito.json())
            self.assertEqual(reiniciado.post("/api/usuarios", json=CLIENTE).status_code, 409)
            nova_conta = reiniciado.post("/api/contas", json=self.titular)
            self.assertEqual(nova_conta.status_code, 201)
            self.assertEqual(nova_conta.json()["numero"], numero + 1)

    def test_saques_simultaneos_nao_deixam_saldo_negativo(self):
        self.client.post("/api/usuarios", json=CLIENTE)
        numero = self.abrir_conta()
        self.assertEqual(self.movimentar(numero, "depositos", "100").status_code, 201)
        with ThreadPoolExecutor(max_workers=2) as executor:
            saques = [executor.submit(self.movimentar, numero, "saques", "80") for _ in range(2)]
            self.assertEqual(sorted(saque.result().status_code for saque in saques), [201, 409])
        extrato = self.client.get(f"/api/contas/{numero}/extrato").json()
        self.assertEqual(extrato["saldo"], "20.00")
        self.assertEqual(len(extrato["movimentacoes"]), 2)

    def test_limite_de_transacoes_reinicia_no_dia_seguinte(self):
        self.client.post("/api/usuarios", json=CLIENTE)
        conta = self.abrir_conta()
        with patch("main.datetime") as relogio:
            relogio.now.return_value = datetime(2025, 1, 1, 23, 59, tzinfo=FUSO)
            for _ in range(5):
                self.assertEqual(self.movimentar(conta, "depositos", "1").status_code, 201)
                self.assertEqual(self.movimentar(conta, "saques", "1").status_code, 201)
            self.assertEqual(self.movimentar(conta, "depositos", "1").status_code, 409)
            relogio.now.return_value = datetime(2025, 1, 2, 0, 0, tzinfo=FUSO)
            self.assertEqual(self.movimentar(conta, "depositos", "1").status_code, 201)
