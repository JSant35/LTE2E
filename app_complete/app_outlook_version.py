import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
from io import BytesIO
import msal
import requests

# ===========================
# CONFIG MS GRAPH
# ===========================
CLIENT_ID = "SEU_CLIENT_ID_AQUI"
TENANT_ID = "SEU_TENANT_ID_AQUI"
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
REDIRECT_URI = "http://localhost:8501"
SCOPE = ["Calendars.Read"]

# ===========================
# FUNÇÃO PARA OBTER TOKEN
# ===========================
def build_msal_app(cache=None):
    return msal.PublicClientApplication(
        CLIENT_ID, authority=AUTHORITY, token_cache=cache
    )

def get_token_interactive():
    app = build_msal_app()
    flow = app.initiate_device_flow(scopes=SCOPE)
    if "user_code" not in flow:
        raise ValueError("Falha ao criar fluxo interativo.")

    st.warning("⚠️ **ATENÇÃO**: Para autorizar, acesse [https://microsoft.com/devicelogin](https://microsoft.com/devicelogin) e insira o código abaixo:")
    st.code(flow["user_code"])

    result = app.acquire_token_by_device_flow(flow)
    if "access_token" in result:
        return result["access_token"]
    else:
        st.error(f"Erro ao obter token: {result.get('error_description')}")
        return None

# ===========================
# BUSCAR EVENTOS
# ===========================
def buscar_eventos_outlook(token):
    endpoint = "https://graph.microsoft.com/v1.0/me/calendar/events"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "$top": 10,
        "$orderby": "start/dateTime",
        "$filter": f"start/dateTime ge '{datetime.datetime.utcnow().isoformat()}'"
    }

    response = requests.get(endpoint, headers=headers, params=params)

    if response.status_code == 200:
        return response.json().get("value", [])
    else:
        st.error(f"Erro ao buscar eventos: {response.status_code} - {response.text}")
        return []

# ===========================
# CONTROLE DE TAREFAS
# ===========================
ARQUIVO = 'tarefas.xlsx'

def carregar_tarefas():
    try:
        return pd.read_excel(ARQUIVO)
    except FileNotFoundError:
        return pd.DataFrame(columns=['Tarefa', 'Responsável', 'Início', 'Fim', 'Status'])

def salvar_tarefas(df):
    df.to_excel(ARQUIVO, index=False)

def exportar_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Tarefas')
    output.seek(0)
    return output

# ===========================
# INTERFACE STREAMLIT
# ===========================
st.set_page_config(page_title="Controle Tarefas + Calendário", layout="wide")
st.title("📋 Controle de Tarefas + Calendário Outlook")

# Obter token
if "token_outlook" not in st.session_state:
    if st.button("🔐 Conectar ao Outlook"):
        token = get_token_interactive()
        if token:
            st.session_state.token_outlook = token
            st.success("✅ Conectado ao Outlook! Recarregue a página se necessário.")
else:
    token = st.session_state.token_outlook

df = carregar_tarefas()

# Cadastro
with st.form("nova_tarefa"):
    st.subheader("➕ Adicionar Nova Tarefa")
    col1, col2 = st.columns(2)
    with col1:
        tarefa = st.text_input("Nome da Tarefa")
        responsavel = st.text_input("Responsável")
    with col2:
        inicio = st.date_input("Data de Início", value=datetime.datetime.today())
        fim = st.date_input("Data de Fim", value=datetime.datetime.today())

    status = st.selectbox("Status", ["Pendente", "Em andamento", "Concluída"])
    enviar = st.form_submit_button("Adicionar")

    if enviar:
        if tarefa and responsavel:
            nova = pd.DataFrame([{
                'Tarefa': tarefa,
                'Responsável': responsavel,
                'Início': inicio,
                'Fim': fim,
                'Status': status
            }])
            df = pd.concat([df, nova], ignore_index=True)
            salvar_tarefas(df)
            st.success("✅ Tarefa adicionada com sucesso!")
            st.experimental_rerun()
        else:
            st.error("❌ Preencha todos os campos.")

# Filtros
st.subheader("🔎 Filtros")
col1, col2 = st.columns(2)
responsaveis_unicos = df['Responsável'].unique().tolist()
status_unicos = df['Status'].unique().tolist()

with col1:
    filtro_responsavel = st.multiselect("Filtrar por Responsável", options=responsaveis_unicos, default=responsaveis_unicos)
with col2:
    filtro_status = st.multiselect("Filtrar por Status", options=status_unicos, default=status_unicos)

df_filtrado = df[df['Responsável'].isin(filtro_responsavel) & df['Status'].isin(filtro_status)]

# Timeline
st.subheader("📆 Timeline de Tarefas")
if not df_filtrado.empty:
    fig = px.timeline(df_filtrado, x_start="Início", x_end="Fim", y="Tarefa", color="Responsável")
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Nenhuma tarefa encontrada com os filtros aplicados.")

# Eventos Outlook
if "token_outlook" in st.session_state:
    st.subheader("📅 Suas Próximas Reuniões no Outlook")
    eventos = buscar_eventos_outlook(token)
    if eventos:
        for evento in eventos:
            nome = evento.get("subject", "(Sem título)")
            inicio = evento["start"].get("dateTime", "")
            fim = evento["end"].get("dateTime", "")
            local = evento.get("location", {}).get("displayName", "")
            st.write(f"**{nome}**  \n📍 {local if local else 'Sem local'}  \n🕒 {inicio} → {fim}")
    else:
        st.info("Nenhum evento futuro encontrado.")
else:
    st.info("Clique em 🔐 Conectar ao Outlook para ver suas reuniões.")

# Exportar
st.subheader("💾 Exportar Tarefas")
buffer = exportar_excel(df)
st.download_button(
    label="📥 Baixar Excel",
    data=buffer,
    file_name="tarefas.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
