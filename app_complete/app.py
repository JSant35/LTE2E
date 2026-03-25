import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
from io import BytesIO
import base64

ARQUIVO = 'tarefas.xlsx'

# Caminho do arquivo que você fez upload
logo_path = "C:\DSV_APP\Analytics_DEV\TECH_LEAD\logo_3mnr.png"

# Codifica a imagem como base64 para embutir no HTML
def get_base64(file_path):
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

logo_base64 = get_base64(logo_path)

# Aplica no topo direito via HTML
st.markdown(
    f"""
    <style>
        .logo-container {{
            position: fixed;
            top: 10px;
            left: 25px;
            z-index: 100;
        }}
        .logo-container img {{
            height: 60px;
        }}
    </style>
    <div class="logo-container">
        <img src="data:image/png;base64,{logo_base64}">
    </div>
    """,
    unsafe_allow_html=True
)


st.set_page_config(page_title="Controle de Tarefas", layout="wide")

# ------------------------------
# Funções de arquivo
# ------------------------------
def carregar_tarefas():
    try:
        return pd.read_excel(ARQUIVO, engine='openpyxl')
    except FileNotFoundError:
        return pd.DataFrame(columns=[
            'Tarefa', 'Responsável', 'Solicitante',
            'Início', 'Fim Previsto', 'Status',
            'Dias Restantes', 'Situação', 'Dias Corridos', 'Observações'])

def salvar_tarefas(df):
    df.to_excel(ARQUIVO, index=False)

def exportar_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Tarefas')
    output.seek(0)
    return output

# ------------------------------
st.title("📋 Controle de Tarefas e Atividades")

# ------------------------------
df = carregar_tarefas()

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
    observacoes = st.text_area("Observações (opcional)")
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
                'Dias Corridos': dias_corridos,
                'Observações': observacoes
            }])
            df = pd.concat([df, nova], ignore_index=True)
            salvar_tarefas(df)
            st.success("✅ Tarefa adicionada com sucesso!")
            st.rerun()
        else:
            st.error("❌ Preencha todos os campos obrigatórios.")

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
st.subheader("📊 Visão Geral")
if not df.empty:
    total = len(df)
    concluidas = df[df['Status'] == 'Concluída'].shape[0]
    em_andamento = df[df['Status'] == 'Em andamento'].shape[0]
    pendentes = df[df['Status'] == 'Pendente'].shape[0]
    atrasadas = df[(df['Situação'] == 'Atrasado') & (df['Status'] != 'Concluída')].shape[0]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("✅ Concluídas", concluidas)
    col2.metric("🕒 Em Andamento", em_andamento)
    col3.metric("🕗 Pendentes", pendentes)
    col4.metric("⚠️ Atrasadas", atrasadas)

# ------------------------------
st.subheader("🔎 Filtros")
colf1, colf2 = st.columns(2)
responsaveis_unicos = df['Responsável'].unique().tolist()
status_unicos = df['Status'].unique().tolist()

with colf1:
    filtro_responsavel = st.multiselect("Filtrar por Responsável", options=responsaveis_unicos, default=responsaveis_unicos)
with colf2:
    filtro_status = st.multiselect("Filtrar por Status", options=status_unicos, default=status_unicos)

df_filtrado = df[df['Responsável'].isin(filtro_responsavel) & df['Status'].isin(filtro_status)]

# ------------------------------
st.subheader("📆 Timeline de Tarefas")
if not df_filtrado.empty:
    fig = px.timeline(df_filtrado, x_start="Início", x_end="Fim Previsto", y="Tarefa", color="Responsável",
                      hover_data=["Solicitante", "Situação", "Dias Corridos", "Observações"])
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Nenhuma tarefa encontrada com os filtros aplicados.")

# ------------------------------
st.subheader("📝 Editar, Excluir ou Concluir Tarefas")
if not df.empty:
    for i, row in df.iterrows():
        with st.expander(f"🔹 {row['Tarefa']} ({row['Responsável']})"):
            col1, col2 = st.columns(2)
            with col1:
                novo_nome = st.text_input(f"Tarefa [{i}]", value=row['Tarefa'], key=f"nome_{i}")
                novo_responsavel = st.text_input(f"Responsável [{i}]", value=row['Responsável'], key=f"resp_{i}")
                novo_solicitante = st.text_input(f"Solicitante [{i}]", value=row['Solicitante'], key=f"sol_{i}")
            with col2:
                novo_inicio = st.date_input(f"Início [{i}]", value=pd.to_datetime(row['Início']).date(), key=f"ini_{i}")
                novo_fim = st.date_input(f"Fim Previsto [{i}]", value=pd.to_datetime(row['Fim Previsto']).date(), key=f"fim_{i}")
            novo_status = st.selectbox(f"Status [{i}]", ["Pendente", "Em andamento", "Concluída"],
                                       index=["Pendente", "Em andamento", "Concluída"].index(row['Status']), key=f"status_{i}")
            nova_obs = st.text_area(f"Observações [{i}]", value=row.get('Observações', ''), key=f"obs_{i}")

            colb1, colb2 = st.columns(2)
            with colb1:
                if st.button(f"Salvar [{i}]"):
                    df.at[i, 'Tarefa'] = novo_nome
                    df.at[i, 'Responsável'] = novo_responsavel
                    df.at[i, 'Solicitante'] = novo_solicitante
                    df.at[i, 'Início'] = novo_inicio
                    df.at[i, 'Fim Previsto'] = novo_fim
                    df.at[i, 'Status'] = novo_status
                    df.at[i, 'Observações'] = nova_obs
                    df.at[i, 'Dias Restantes'] = (novo_fim - date.today()).days
                    df.at[i, 'Situação'] = 'Atrasado' if df.at[i, 'Dias Restantes'] < 0 and novo_status != 'Concluída' else 'No prazo'
                    df.at[i, 'Dias Corridos'] = (date.today() - novo_inicio).days if novo_status != 'Concluída' else (novo_fim - novo_inicio).days
                    salvar_tarefas(df)
                    st.success("✅ Alterado!")
                    st.rerun()
            with colb2:
                if st.button(f"Excluir [{i}]", type="primary"):
                    df = df.drop(i).reset_index(drop=True)
                    salvar_tarefas(df)
                    st.warning("⚠️ Excluída")
                    st.rerun()

# ------------------------------
st.subheader("📥 Exportar")
col_exp1, col_exp2 = st.columns(2)
with col_exp1:
    buffer = exportar_excel(df)
    st.download_button("📥 Baixar Excel", data=buffer, file_name="tarefas.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
with col_exp2:
    st.info("⚠️ Exporte em PDF convertendo o Excel se quiser.")
