import time
menu = """
Bem-vindo ao Banco Python!
Escolha uma opção:

[d] Depositar
[s] Sacar
[e] Extrato
[q] Sair

=> """

saldo = 0
limite = 500
extrato = []
numero_saques = 0
LIMITE_SAQUES = 3

def depositar(valor):
    global saldo, extrato
    if valor > 0:
        saldo += valor
        extrato.append(f"Depósito: R$ {valor:.2f}\n") 
        print(f"Depósito de R$ {valor:.2f} realizado com sucesso!")
        time.sleep(1)
    else:
        print("Valor de depósito inválido!")

while True:
    opcao = input(menu)
    if opcao == "d".lower():
        time.sleep(1)
        valor_deposito = float(input("Informe o valor do depósito: R$ "))
        depositar(valor_deposito)
        
    elif opcao == "s".lower():
        pass
    elif opcao == "e".lower():
        pass
    elif opcao == "q".lower():
        print("Obrigado por usar o sistema! Até logo!")
        break
    else:
        print("Opção inválida! Por favor, escolha uma opção válida do menu.")