# Sistema Bancário em Python

Este projeto é um sistema bancário simples desenvolvido em Python, com funcionalidades básicas de depósito, saque e extrato. O objetivo é simular operações bancárias de forma didática, utilizando conceitos fundamentais de programação.

## Funcionalidades

- **Depósito:** Permite adicionar saldo à conta, registrando cada operação no extrato.
- **Saque:** Permite realizar saques, respeitando o limite diário de valor e quantidade de saques.
- **Extrato:** Exibe todas as movimentações realizadas e o saldo atual.
- **Validação de entradas:** Garante que apenas valores válidos sejam processados.

## Como usar

1. Clone este repositório ou baixe os arquivos.
2. Execute o arquivo `main.py` com Python 3:
   ```
   python main.py
   ```
3. Siga as instruções do menu interativo no terminal.

## Exemplo de uso

```
Bem-vindo ao Banco Python!
Escolha uma opção:

[d] Depositar
[s] Sacar
[e] Extrato
[q] Sair

=> d
Informe o valor do depósito: R$ 100
Depósito de R$ 100.00 realizado com sucesso!
```

## Requisitos

- Python 3.x

## Melhorias Futuras

- Implementação de múltiplas contas.
- Interface gráfica.
- Persistência dos dados em arquivo ou banco de dados.

---

Projeto desenvolvido para fins de aprendizado