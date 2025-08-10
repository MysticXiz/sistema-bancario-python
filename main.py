from datetime import datetime
import pytz



# def __init__(self):
#     global saldo, limite_saque, extrato, numero

def menu():
    menu = """
    Bem-vindo ao Banco Python!
    Escolha uma opção:

    [d] Depositar
    [s] Sacar
    [e] Extrato
    [nc] Nova Conta
    [ls] Listar Contas
    [nu] Novo Usuário
    [q] Sair

    => """
    return input(menu)


saldo = 0
limite_saque = 500
extrato = []
numero_transacoes = 0
usuarios = []
contas = []
LIMITE_TRANSACOES = 10
AGENCIA = "0001"


def depositar(saldo, valor, extrato, /, numero_transacoes, LIMITE_TRANSACOES):
    if numero_transacoes >= LIMITE_TRANSACOES: return f"Limite de transações diários atingido ({LIMITE_TRANSACOES} transações)."
    elif valor > 0:
        saldo += valor
        extrato.append(f"Depósito: R$ {valor:.2f} - {datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%d/%m/%Y %H:%M:%S')}") 
        numero_transacoes += 1
        print(f"Depósito de R$ {valor:.2f} realizado com sucesso!")
        return saldo, extrato
    else:
        return "Valor de depósito inválido!"

def sacar(*, saldo, valor, extrato, numero_transacoes, limite_saque, LIMITE_TRANSACOES):
    
    if valor <= 0: return "Valor de saque inválido! O valor deve ser maior que zero."    
    if valor > saldo: return "Saldo insuficiente para realizar o saque."       
    if valor > limite_saque: return f"Valor de saque excede o limite de R$ {limite_saque:.2f}."    
    if numero_transacoes >= LIMITE_TRANSACOES: return f"Limite de transações diários atingido ({LIMITE_TRANSACOES} transações)."
    
    saldo -= valor
    extrato.append(f"Saque: -R$ {valor:.2f} - {datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%d/%m/%Y %H:%M:%S')}")
    numero_transacoes += 1
    print(f"Saque de R$ {valor:.2f} realizado com sucesso!")
    return saldo, extrato
    
def mostrar_extrato(saldo, /, *,extrato):
    print("\n=== EXTRATO ===")
    if not extrato:
        print("Nenhuma movimentação realizada.")
    else:
        for item in extrato:
            print(item)
    print(f"\nSaldo atual: R$ {saldo:.2f} ")
    print("================\n")

def novo_usuario(usuarios):
    cpf = input("Informe o CPF do novo usuário: ")
    for usuario in usuarios:
        if usuario['cpf'] == cpf:
            print("Usuário já cadastrado com este CPF.")
            return

    nome = input("Informe o nome do novo usuário: ")
    data_nascimento = input("Informe a data de nascimento do novo usuário (dd-mm-yyyy): ")
    endereco = input("Informe o endereço do novo usuário: ")

    usuarios.append({
        "cpf": cpf,
        "nome": nome,
        "data_nascimento": data_nascimento,
        "endereco": endereco
    })
    print(f"Usuário {nome} cadastrado com sucesso!")

def filtrar_usuarios(cpf, usuarios):
    return next((u for u in usuarios if u['cpf'] == cpf), None)

def nova_conta(agencia, numero_conta, usuarios):
    cpf = input("Informe o CPF do usuário para criar a conta: ")
    usuario = filtrar_usuarios(cpf, usuarios)

    if usuario:
        print(f"Conta criada com sucesso!")
        return {
            "agencia": agencia,
            "numero_conta": numero_conta,
            "usuario": usuario
        }
    
    print("Usuário não encontrado. Por favor, cadastre o usuário primeiro.")

def listar_contas(contas):
    if not contas:
        print("Nenhuma conta cadastrada.")
        return

    print("\n=== CONTAS CADASTRADAS ===")
    for conta in contas:
        print(f"Agência: {conta.get('agencia')}, Conta: {conta.get('numero_conta')}, Usuário: {conta.get('usuario', {}).get('nome')}")
    print("==========================\n")
    
while True:
    opcao = menu()
    if opcao == "d".lower(): #deposito
        try:
            valor_deposito = float(input("Informe o valor do depósito: R$ "))
            saldo, extrato = depositar(saldo, valor_deposito, extrato, numero_transacoes, LIMITE_TRANSACOES)
        except ValueError:
            print("Erro: Valor inválido. Por favor, insira um número válido.")

    elif opcao == "s".lower(): #saque
        try:
            valor_saque = float(input("Informe o valor do saque: R$ "))
            saldo, extrato = sacar(
               saldo=saldo, 
               valor_saque=valor_saque, 
               extrato=extrato, 
               numero_transacoes=numero_transacoes, 
               limite_saque=limite_saque,  
               LIMITE_TRANSACOES=LIMITE_TRANSACOES
            )
        except ValueError:
            print("Erro: Valor inválido. Por favor, insira um número válido.")

    elif opcao == "e".lower(): #extrato
        mostrar_extrato(saldo, extrato=extrato)

    elif opcao == "nc".lower(): #nova conta
        numero_conta = len(contas) + 1
        conta = nova_conta(AGENCIA, numero_conta, usuarios)
        if conta:
            contas.append(conta)

        
    elif opcao == "ls".lower(): #listar contas
        listar_contas(contas)
    elif opcao == "nu".lower(): #novo usuário
        novo_usuario(usuarios)

    elif opcao == "q".lower(): #sair
        print("Obrigado por usar o sistema! Até logo!")
        break
    else:
        print("Opção inválida! Por favor, escolha uma opção válida do menu.")

