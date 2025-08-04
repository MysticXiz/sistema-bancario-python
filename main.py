
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
        extrato.append(f"Depósito: R$ {valor:.2f}") 
        return f"Depósito de R$ {valor:.2f} realizado com sucesso!"
    else:
        return "Valor de depósito inválido!"

def sacar(valor):
    global saldo, extrato, numero_saques, LIMITE_SAQUES
    
    if valor <= 0: return "Valor de saque inválido! O valor deve ser maior que zero."    
    if valor > saldo: return "Saldo insuficiente para realizar o saque."       
    if valor > limite: return f"Valor de saque excede o limite de R$ {limite:.2f}."    
    if numero_saques >= LIMITE_SAQUES: return f"Limite de saques diários atingido ({LIMITE_SAQUES} saques)."
    
    saldo -= valor
    extrato.append(f"Saque: -R$ {valor:.2f}")
    numero_saques += 1
    return f"Saque de R$ {valor:.2f} realizado com sucesso!"
    
def mostrar_extrato():
    print("\n=== EXTRATO ===")
    if not extrato:
        print("Nenhuma movimentação realizada.")
    else:
        for item in extrato:
            print(item)
    print(f"\nSaldo atual: R$ {saldo:.2f}")
    print("================\n")
while True:
    opcao = input(menu)
    if opcao == "d".lower(): #deposito
        try:
            valor_deposito = float(input("Informe o valor do depósito: R$ "))
            print(depositar(valor_deposito))
        except ValueError:
            print("Erro: Valor inválido. Por favor, insira um número válido.")

    elif opcao == "s".lower(): #saque
        try:
            valor_saque = float(input("Informe o valor do saque: R$ "))
            print(sacar(valor_saque))
        except ValueError:
            print("Erro: Valor inválido. Por favor, insira um número válido.")

    elif opcao == "e".lower(): #extrato
        mostrar_extrato()

    elif opcao == "q".lower(): #sair
        print("Obrigado por usar o sistema! Até logo!")
        break
    else:
        print("Opção inválida! Por favor, escolha uma opção válida do menu.")

