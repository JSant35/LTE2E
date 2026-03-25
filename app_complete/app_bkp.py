import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
from io import BytesIO

ARQUIVO = 'tarefas.xlsx'

st.set_page_config(page_title="Controle de Tarefas", layout="wide")

# ------------------------------
# Funções de arquivo
# ------------------------------
def carregar_tarefas():
    try:
        return pd.read_excel(ARQUIVO, engine='openpyxl')
    except FileNotFoundError:
        return pd.DataFrame(columns=['Tarefa', 'Responsável', 'Solicitante', 'Início', 'Fim Previsto', 'Status', 'Dias Restantes', 'Situação', 'Dias Corridos'])

def salvar_tarefas(df):
    df.to_excel(ARQUIVO, index=False)

def exportar_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Tarefas')
    output.seek(0)
    return output

# ------------------------------
# Interface
# ------------------------------
st.title("📋 Controle de Tarefas e Atividades")

df = carregar_tarefas()

# ------------------------------
# Cadastro de tarefa
# ------------------------------
with st.form("nova_tarefa"):
    st.subheader("➕ Adicionar Nova Tarefa")
    col1, col2, col3 = st.columns(3)
    with col1:
        tarefa = st.text_input("Nome da Tarefa")
        responsavel = st.text_input("Responsável")
        solicitante = st.text_input("Solicitante")
    with col2:
        inicio = st.date_input("Data de Início", value=date.today())
        fim_previsto = st.date_input("Data de Fim Previsto", value=date.today())
    with col3:
        status = st.selectbox("Status", ["Pendente", "Em andamento", "Concluída"])
    enviar = st.form_submit_button("Adicionar")

    if enviar:
        if tarefa and responsavel and solicitante:
            dias_restantes = (fim_previsto - date.today()).days
            situacao = 'Atrasado' if dias_restantes < 0 and status != 'Concluída' else 'No prazo'
            dias_corridos = (date.today() - inicio).days if status != 'Concluída' else (fim_previsto - inicio).days

            nova = pd.DataFrame([{
                'Tarefa': tarefa,
                'Responsável': responsavel,
                'Solicitante': solicitante,
                'Início': inicio,
                'Fim Previsto': fim_previsto,
                'Status': status,
                'Dias Restantes': dias_restantes,
                'Situação': situacao,
                'Dias Corridos': dias_corridos
            }])
            df = pd.concat([df, nova], ignore_index=True)
            salvar_tarefas(df)
            st.success("✅ Tarefa adicionada com sucesso!")
            st.rerun()
        else:
            st.error("❌ Preencha todos os campos obrigatórios.")

# ------------------------------
# Atualizar cálculos
# ------------------------------
if not df.empty:
    df['Dias Restantes'] = df['Fim Previsto'].apply(lambda x: (x.date() - date.today()).days if pd.notnull(x) else None)
    df['Situação'] = df.apply(lambda x: 'Atrasado' if x['Dias Restantes'] < 0 and x['Status'] != 'Concluída' else 'No prazo', axis=1)
    df['Dias Corridos'] = df.apply(
        lambda x: (date.today() - x['Início'].date()).days if x['Status'] != 'Concluída' else (x['Fim Previsto'].date() - x['Início'].date()).days,
        axis=1
    )
    salvar_tarefas(df)

# ------------------------------
# Indicador de progresso
# ------------------------------
st.subheader("✅ Progresso Geral")
if not df.empty:
    total = len(df)
    concluidas = df[df['Status'] == 'Concluída'].shape[0]
    progresso = int((concluidas / total) * 100)
    st.progress(progresso / 100)
    st.write(f"{concluidas} de {total} tarefas concluídas ({progresso}%)")
else:
    st.info("Nenhuma tarefa cadastrada ainda para mostrar progresso.")

# ------------------------------
# Filtros
# ------------------------------
st.subheader("🔎 Filtros")
col1, col2 = st.columns(2)
responsaveis_unicos = df['Responsável'].unique().tolist()
status_unicos = df['Status'].unique().tolist()

with col1:
    filtro_responsavel = st.multiselect("Filtrar por Responsável", options=responsaveis_unicos, default=responsaveis_unicos)
with col2:
    filtro_status = st.multiselect("Filtrar por Status", options=status_unicos, default=status_unicos)

df_filtrado = df[df['Responsável'].isin(filtro_responsavel) & df['Status'].isin(filtro_status)]

# ------------------------------
# Timeline
# ------------------------------
st.subheader("📆 Timeline de Tarefas")
if not df_filtrado.empty:
    fig = px.timeline(
        df_filtrado,
        x_start="Início", x_end="Fim Previsto",
        y="Tarefa", color="Responsável",
        hover_data=["Solicitante", "Situação", "Dias Corridos"]
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(height=500, margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Nenhuma tarefa encontrada com os filtros aplicados.")

# ------------------------------
# Gráfico pizza status
# ------------------------------
if not df.empty:
    st.subheader("🥧 Distribuição de Status")
    status_counts = df['Status'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Contagem']
    fig_pie = px.pie(status_counts, names='Status', values='Contagem', title='Distribuição de Tarefas por Status')
    st.plotly_chart(fig_pie, use_container_width=True)

# ------------------------------
# Edição, exclusão e marcar como concluída
# ------------------------------
st.subheader("📝 Editar, Excluir ou Concluir Tarefas")

if not df.empty:
    for i, row in df.iterrows():
        with st.expander(f"🔹 {row['Tarefa']} ({row['Responsável']})"):
            col1, col2 = st.columns(2)
            with col1:
                novo_nome = st.text_input(f"Nome Tarefa [{i}]", value=row['Tarefa'], key=f"nome_{i}")
                novo_responsavel = st.text_input(f"Responsável [{i}]", value=row['Responsável'], key=f"resp_{i}")
                novo_solicitante = st.text_input(f"Solicitante [{i}]", value=row['Solicitante'], key=f"sol_{i}")
            with col2:
                novo_inicio = st.date_input(f"Início [{i}]", value=pd.to_datetime(row['Início']).date(), key=f"ini_{i}")
                novo_fim_previsto = st.date_input(f"Fim Previsto [{i}]", value=pd.to_datetime(row['Fim Previsto']).date(), key=f"fim_{i}")

            novo_status = st.selectbox(f"Status [{i}]", ["Pendente", "Em andamento", "Concluída"], index=["Pendente", "Em andamento", "Concluída"].index(row['Status']), key=f"status_{i}")

            col3, col4, col5 = st.columns(3)
            with col3:
                if st.button(f"Salvar Alterações [{i}]"):
                    df.at[i, 'Tarefa'] = novo_nome
                    df.at[i, 'Responsável'] = novo_responsavel
                    df.at[i, 'Solicitante'] = novo_solicitante
                    df.at[i, 'Início'] = novo_inicio
                    df.at[i, 'Fim Previsto'] = novo_fim_previsto
                    df.at[i, 'Status'] = novo_status
                    df.at[i, 'Dias Restantes'] = (novo_fim_previsto - date.today()).days
                    df.at[i, 'Situação'] = 'Atrasado' if df.at[i, 'Dias Restantes'] < 0 and novo_status != 'Concluída' else 'No prazo'
                    df.at[i, 'Dias Corridos'] = (date.today() - novo_inicio).days if novo_status != 'Concluída' else (novo_fim_previsto - novo_inicio).days
                    salvar_tarefas(df)
                    st.success("✅ Alterações salvas!")
                    st.rerun()

            with col4:
                if st.button(f"Excluir Tarefa [{i}]", type="primary"):
                    df = df.drop(i).reset_index(drop=True)
                    salvar_tarefas(df)
                    st.warning("⚠️ Tarefa excluída.")
                    st.rerun()

            with col5:
                if st.button(f"Marcar Concluída [{i}]"):
                    df.at[i, 'Status'] = 'Concluída'
                    df.at[i, 'Dias Restantes'] = 0
                    df.at[i, 'Situação'] = 'No prazo'
                    df.at[i, 'Dias Corridos'] = (date.today() - df.at[i, 'Início'].date()).days
                    salvar_tarefas(df)
                    st.success("✅ Tarefa marcada como concluída!")
                    st.rerun()

# ------------------------------
# Exportar
# ------------------------------
st.subheader("💾 Exportar Dados")

col_exp1, col_exp2 = st.columns(2)

with col_exp1:
    buffer = exportar_excel(df)
    st.download_button(
        label="📥 Baixar Excel",
        data=buffer,
        file_name="tarefas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

with col_exp2:
    st.info("⚠️ Exportação em PDF pode ser feita convertendo o Excel (ou posso ajudar a gerar PDF direto em Python).")
