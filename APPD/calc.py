#Importando bibliotecas
import psycopg2
import matplotlib
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint
matplotlib.use('Agg')

#Conectando ao banco                                               Insira seu user/password
conn = psycopg2.connect(host='localhost', dbname='plague_inc', user='postgres', password='xablau', port='5432')
cursor = conn.cursor()

#Calculo das derivadas
def derivadas(valores, tempo, beta, gamma):
    S, I, R = valores
    N = S + I + R

    # Formula do modelo SIR
    dS_dt = -beta * S * I / N
    dI_dt = beta * S * I / N - gamma * I
    dR_dt = gamma * I

    return [dS_dt, dI_dt, dR_dt]

# susce = Suscetível/ infec = Infectado/ recu = Recuperado

#Calculo do modelo SIR
def sir_model(beta, gamma, susce, infec, recu, dias):
    # Condições iniciais do vetor
    condicoes_iniciais = [susce, infec, recu]
    # array de tempo de 0 a X dias com intervalo de 1
    tempo = np.arange(0, dias, 1)
    resultado = odeint(derivadas, condicoes_iniciais,
                       tempo, args=(beta, gamma))

    return resultado[:, 0], resultado[:, 1], resultado[:, 2]

#Função de plotagem do grafo
def plot(suscetivel, infectado, recuperado, dias, imagem):
    plt.figure()
    plt.plot(range(dias), suscetivel, label='Suscetíveis')
    plt.plot(range(dias), infectado, label='Infectados')
    plt.plot(range(dias), recuperado, label='Recuperados')
    plt.xlabel('Dias')
    plt.ylabel('População')
    plt.title('MODELO SIR - Simulação de Propagação de Doença')
    plt.legend()
    plt.savefig(imagem)
    plt.close()

#Função que recebe os valores de beta e gamma a partir do banco de dados convertendo os valores para float
def consulta_doenca(id_doenca):
    # Realizando a consulta ao banco de dados com conversão de tipos
    cursor.execute(
        "SELECT beta::FLOAT, gamma::FLOAT, tempo FROM doencas WHERE id_doenca = %s", (id_doenca,))
    resultado = cursor.fetchone()

    return resultado

#Plotagem do calculo e de doencas pré existentes
def calculo(nome, file):
    if nome == "h1n1":
        beta, gamma, dias = consulta_doenca(1)
    elif nome == "covid":
        beta, gamma, dias = consulta_doenca(2)
    elif nome == "gripe":
        beta, gamma, dias = consulta_doenca(3)

    susc_inicial = 0.99
    infec_inicial = 0.01
    recul_inicial = 0

    # Simulação
    suscetivel, infectado, recuperado = sir_model(
        beta, gamma, susc_inicial, infec_inicial, recul_inicial, dias)

    # Plotagem
    plot_file = file
    plot(suscetivel, infectado, recuperado, dias, plot_file)
    return plot_file

#Função que recebe as variaveis inseridas pelo usuário para criar nova doença
def nova_doenca(beta, gamma, tempo, nome_doenca):
    susc_inicial = 90
    infec_inicial = 10
    recul_inicial = 0

    # Simulação
    suscetivel, infectado, recuperado = sir_model(
        beta, gamma, susc_inicial, infec_inicial, recul_inicial, tempo)
    
    plot_file = "static\imagens\doenca_nova.png"
    plot(suscetivel, infectado, recuperado, tempo, plot_file)
    #Inserção no banco de dados
    sql = f"INSERT INTO doencas(nome_doenca, beta, gamma, tempo) VALUES (%s, %s, %s, %s)"
    try:
        cursor.execute(sql, (nome_doenca, beta, gamma, tempo))
        conn.commit()
    except:
        conn.rollback()
    
    return plot_file

#Verificar o historico de doenças inseridas no banco
def historico():
    # Executar a consulta
    cursor.execute("SELECT nome_doenca from public.doencas")
    
    # Obter os resultados da consulta
    historico = cursor.fetchall()
    
    lista_historico = []
    
    for row in historico:
        for i in row:
            lista_historico.append(i)

    return lista_historico