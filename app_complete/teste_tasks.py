import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from datetime import datetime

# Arquivo de armazenamento
ARQUIVO = 'tarefas.xlsx'

# Função para adicionar nova tarefa
def adicionar_tarefa(nome, responsavel, inicio, fim, status):
    nova_tarefa = pd.DataFrame([{
        'Tarefa': nome,
        'Responsável': responsavel,
        'Início': pd.to_datetime(inicio),
        'Fim': pd.to_datetime(fim),
        'Status': status
    }])

    try:
        tarefas = pd.read_excel(ARQUIVO)
        tarefas = pd.concat([tarefas, nova_tarefa], ignore_index=True)
    except FileNotFoundError:
        tarefas = nova_tarefa

    tarefas.to_excel(ARQUIVO, index=False)
    print("✅ Tarefa adicionada com sucesso!")

# Função para gerar gráfico Gantt (timeline)
def gerar_grafico_timeline():
    try:
        tarefas = pd.read_excel(ARQUIVO)
        fig = px.timeline(tarefas, x_start="Início", x_end="Fim", y="Tarefa", color="Responsável")
        fig.update_yaxes(autorange="reversed")  # ordem inversa
        fig.update_layout(title="Timeline de Tarefas")
        fig.show()
    except FileNotFoundError:
        print("❌ Nenhuma tarefa encontrada. Adicione uma tarefa primeiro.")

# Gráfico de status por responsável
def grafico_status_responsavel():
    try:
        tarefas = pd.read_excel(ARQUIVO)
        status_count = tarefas.groupby(['Responsável', 'Status']).size().unstack(fill_value=0)
        status_count.plot(kind='bar', stacked=True, figsize=(10,6))
        plt.title('Tarefas por Responsável e Status')
        plt.ylabel('Quantidade')
        plt.xlabel('Responsável')
        plt.tight_layout()
        plt.show()
    except FileNotFoundError:
        print("❌ Nenhuma tarefa encontrada. Adicione uma tarefa primeiro.")

# EXEMPLO DE USO
if __name__ == "__main__":
    # adicionar_tarefa("Planejamento do projeto", "Ana", "2025-06-10", "2025-06-15", "Pendente")
    # adicionar_tarefa("Execução inicial", "Carlos", "2025-06-16", "2025-06-20", "Em andamento")

    gerar_grafico_timeline()
    grafico_status_responsavel()
