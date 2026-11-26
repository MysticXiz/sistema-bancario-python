# Banco Python

Simulador bancário didático com FastAPI, SQLite e uma interface web responsiva em HTML, CSS e JavaScript. O frontend é servido pela própria API: não precisa de Node.js nem de instalar um servidor de banco de dados.

## Como rodar

Requer Python 3.10 ou mais recente.

```sh
git clone https://github.com/MysticXiz/sistema-bancario-python.git
cd sistema-bancario-python
python -m venv .venv
```

Ative o ambiente virtual com `.venv\Scripts\Activate.ps1` no PowerShell ou com `source .venv/bin/activate` no Bash (Linux/macOS). Depois rode:

```sh
python -m pip install -r requirements.txt
python -m uvicorn main:app
```

- **App:** http://127.0.0.1:8000/
- **API interativa (Swagger):** http://127.0.0.1:8000/docs

Na interface, abra **Cadastro e contas**, cadastre um cliente com dados fictícios e use o mesmo CPF para abrir uma conta. Selecione a conta e faça um depósito para começar.

## Banco de dados

Na primeira inicialização, o app cria `banco.sqlite3` ao lado de `main.py` usando o módulo `sqlite3` do Python. Clientes, contas, saldos e movimentações são mantidos ao reiniciar. Os valores são armazenados em centavos inteiros. Para zerar a demo, pare o servidor e apague `banco.sqlite3`.

## Regras

- O CPF é único e tem 11 dígitos, sem pontuação; o projeto não verifica os dígitos verificadores.
- Cada conta tem saldo e extrato próprios, agência `0001` e número sequencial.
- Valores são positivos e têm até duas casas decimais. Saques são limitados a R$ 500,00 por operação e não podem ultrapassar o saldo.
- Cada conta pode realizar até 10 movimentações bem-sucedidas por dia, somando depósitos e saques. A contagem muda à meia-noite no horário de São Paulo.

## Rotas da API

| Método | Rota | Dados de entrada |
| --- | --- | --- |
| `POST` | `/api/usuarios` | `{"cpf":"00000000000","nome":"Ana Silva","data_nascimento":"1998-05-20","endereco":"Rua Exemplo, 123"}` |
| `POST` | `/api/contas` | `{"cpf":"00000000000"}` |
| `GET` | `/api/contas` | — |
| `GET` | `/api/contas/{numero}/extrato` | — |
| `POST` | `/api/contas/{numero}/depositos` | `{"valor":"150.00"}` |
| `POST` | `/api/contas/{numero}/saques` | `{"valor":"50.00"}` |

Use strings decimais com ponto na API para evitar arredondamento pelo cliente. Saldos e valores também são retornados como strings decimais.

## Testes

```sh
python -m pip install httpx
python -m unittest -v
```

Os testes usam arquivos SQLite temporários e não alteram o banco da demo.

**Somente para uso local e didático.** Não há autenticação nem autorização. Os dados são compartilhados entre abas. Não exponha o servidor nem informe dados reais.
