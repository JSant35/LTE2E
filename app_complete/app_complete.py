import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
import plotly.express as px
import bcrypt

# --------------------------------------------------
# BANCO DE DADOS
# --------------------------------------------------
def conectar():
    return sqlite3.connect("tarefas.db", check_same_thread=False)

conn = conectar()

def criar_tabelas():
    conn.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE,
            senha BLOB
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS tarefas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            responsavel TEXT,
            solicitante TEXT,
            inicio DATE,
            fim DATE,
            prioridade TEXT,
            sla INTEGER,
            status TEXT,
            progresso INTEGER,
            dias_restantes INTEGER,
            risco TEXT,
            observacoes TEXT,
            id_usuario INTEGER
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS subtarefas (
            id_sub INTEGER PRIMARY KEY AUTOINCREMENT,
            id_tarefa INTEGER,
            nome TEXT,
            status TEXT
        )
    """)

    conn.commit()

criar_tabelas()

# --------------------------------------------------
# FUNÇÕES AUXILIARES
# --------------------------------------------------
def calcular_risco(dias_rest, sla):
    if dias_rest <= sla * 0.25:
        return "🔴 Alto"
    elif dias_rest <= sla * 0.5:
        return "🟠 Médio"
    return "🟢 Baixo"

def progresso_por_subtarefas(id_tarefa):
    df = pd.read_sql_query(
        f"SELECT * FROM subtarefas WHERE id_tarefa={id_tarefa}", conn
    )
    if df.empty:
        return 0
    done = len(df[df["status"] == "Done"])
    return int((done / len(df)) * 100)

# --------------------------------------------------
# TEMA CORPORATIVO
# --------------------------------------------------
st.set_page_config(page_title="Task Master PRO", layout="wide")

CORP_STYLE = """
<style>
body {
    background-color: #f4f6f9;
}
.sidebar .sidebar-content {
    background-color: #1b263b;
}
h1, h2, h3, h4, h5 {
    color: #1b263b;
}
</style>
"""

st.markdown(CORP_STYLE, unsafe_allow_html=True)

# --------------------------------------------------
# AUTENTICAÇÃO
# --------------------------------------------------
def registrar_usuario(usuario, senha):
    senha_hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt())
    try:
        conn.execute("INSERT INTO usuarios (usuario, senha) VALUES (?,?)", (usuario, senha_hash))
        conn.commit()
        return True
    except:
        return False

def login(usuario, senha):
    result = conn.execute("SELECT senha FROM usuarios WHERE usuario=?", (usuario,)).fetchone()
    if result:
        return bcrypt.checkpw(senha.encode(), result[0])
    return False

# --------------------------------------------------
# SESSÃO
# --------------------------------------------------
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:

    st.title("🔐 Login - Task Master PRO")

    aba = st.tabs(["Entrar", "Registrar"])

    with aba[0]:
        user = st.text_input("Usuário")
        pwd = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            if login(user, pwd):
                st.session_state.logado = True
                st.session_state.user = user
                st.success("✅ Login realizado!")
                st.rerun()
            else:
                st.error("❌ Usuário ou senha inválidos")

    with aba[1]:
        new_user = st.text_input("Novo usuário")
        new_pwd = st.text_input("Nova senha", type="password")
        if st.button("Registrar"):
            if registrar_usuario(new_user, new_pwd):
                st.success("✅ Usuário registrado! Faça login.")
            else:
                st.error("❌ Usuário já existe.")

    st.stop()

# --------------------------------------------------
# APP PRINCIPAL
# --------------------------------------------------
st.sidebar.title(f"👤 Usuário: {st.session_state.user}")
if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.rerun()

st.title("📌 Task Master PRO – Gestão Corporativa")

# --------------------------------------------------
# CARREGAR TAREFAS DO USUÁRIO
# --------------------------------------------------
df = pd.read_sql_query(
    f"SELECT * FROM tarefas WHERE id_usuario=(SELECT id FROM usuarios WHERE usuario='{st.session_state.user}')",
    conn
)

# --------------------------------------------------
# NOVA TAREFA
# --------------------------------------------------
with st.form("nova_tarefa"):
    st.subheader("➕ Criar Nova Tarefa")

    col1, col2, col3 = st.columns(3)

    nome = col1.text_input("Nome")
    responsavel = col1.text_input("Responsável")
    solicitante = col1.text_input("Solicitante")

    inicio = col2.date_input("Início", date.today())
    fim = col2.date_input("Fim")

    prioridade = col3.selectbox("Prioridade", ["Baixa", "Média", "Alta", "Crítica"])
    sla = col3.number_input("SLA (dias)", min_value=1, max_value=365)
    status = col3.selectbox("Status", ["To-Do", "Doing", "Done"])

    obs = st.text_area("Observações")

    enviar = st.form_submit_button("Salvar")

    if enviar:
        dias_rest = (fim - date.today()).days
        risco = calcular_risco(dias_rest, sla)

        user_id = conn.execute(
            "SELECT id FROM usuarios WHERE usuario=?", (st.session_state.user,)
        ).fetchone()[0]

        conn.execute("""
            INSERT INTO tarefas
            (nome,responsavel,solicitante,inicio,fim,prioridade,sla,status,
            progresso,dias_restantes,risco,observacoes,id_usuario)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (nome, responsavel, solicitante, inicio, fim, prioridade, sla,
              status, 0, dias_rest, risco, obs, user_id))

        conn.commit()
        st.success("✅ Tarefa criada!")
        st.rerun()

# --------------------------------------------------
# KANBAN
# --------------------------------------------------
st.subheader("📌 Quadro Kanban")

col_todo, col_doing, col_done = st.columns(3)

for status, col in zip(["To-Do", "Doing", "Done"], [col_todo, col_doing, col_done]):
    col.markdown(f"### {status}")
    subt = df[df["status"] == status]
    for _, row in subt.iterrows():
        col.info(
            f"**{row['nome']}**\n"
            f"📅 {row['fim']}\n"
            f"⏳ {row['risco']}"
        )

# --------------------------------------------------
# EDIÇÃO
# --------------------------------------------------
st.subheader("📝 Gerenciar Tarefas")

for _, row in df.iterrows():

    with st.expander(f"🔹 {row['nome']}"):

        c1, c2 = st.columns(2)

        novo_nome = c1.text_input("Nome", row["nome"], key=f"n_{row['id']}")
        novo_resp = c1.text_input("Responsável", row["responsavel"], key=f"r_{row['id']}")
        novo_obs = st.text_area("Observações", row["observacoes"], key=f"o_{row['id']}")

        novo_inicio = c2.date_input("Início", row["inicio"], key=f"i_{row['id']}")
        novo_fim = c2.date_input("Fim", row["fim"], key=f"f_{row['id']}")

        nova_prior = c1.selectbox("Prioridade", ["Baixa","Média","Alta","Crítica"],
                                  index=["Baixa","Média","Alta","Crítica"].index(row["prioridade"]),
                                  key=f"p_{row['id']}")

        novo_status = c2.selectbox(
            "Status", ["To-Do","Doing","Done"],
            index=["To-Do","Doing","Done"].index(row["status"]),
            key=f"s_{row['id']}"
        )

        # SUBTAREFAS
        st.markdown("### ✅ Subtarefas")

        df_sub = pd.read_sql_query(
            f"SELECT * FROM subtarefas WHERE id_tarefa={row['id']}", conn
        )

        for _, s in df_sub.iterrows():
            novo_status_sub = st.selectbox(
                f"{s['nome']}",
                ["To-Do","Doing","Done"],
                index=["To-Do","Doing","Done"].index(s["status"]),
                key=f"sub_{s['id_sub']}"
            )
            conn.execute("UPDATE subtarefas SET status=? WHERE id_sub=?", (novo_status_sub, s["id_sub"]))
            conn.commit()

        nova_sub = st.text_input("Adicionar subtarefa", key=f"new_sub_{row['id']}")
        if st.button("➕ Add Subtarefa", key=f"btn_add_sub_{row['id']}"):
            conn.execute("""
                INSERT INTO subtarefas (id_tarefa, nome, status)
                VALUES (?, ?, 'To-Do')
            """, (row["id"], nova_sub))
            conn.commit()
            st.rerun()

        # PROGRESSO
        progresso = progresso_por_subtarefas(row["id"])
        st.progress(progresso / 100)
        st.write(f"Progresso: **{progresso}%**")

        if st.button("💾 Salvar", key=f"save_{row['id']}"):
            dias_rest = (novo_fim - date.today()).days
            risco = calcular_risco(dias_rest, row["sla"])

            conn.execute("""
                UPDATE tarefas SET
                nome=?, responsavel=?, inicio=?, fim=?, prioridade=?, status=?,
                progresso=?, dias_restantes=?, risco=?, observacoes=?
                WHERE id=?
            """, (novo_nome, novo_resp, novo_inicio, novo_fim, nova_prior,
                  novo_status, progresso, dias_rest, risco, novo_obs, row["id"]))
            conn.commit()
            st.success("Atualizado!")
            st.rerun()

        if st.button("🗑 Excluir", key=f"del_{row['id']}"):
            conn.execute("DELETE FROM tarefas WHERE id=?", (row["id"],))
            conn.execute("DELETE FROM subtarefas WHERE id_tarefa=?", (row["id"],))
            conn.commit()
            st.warning("Tarefa excluída!")
            st.rerun()

# --------------------------------------------------
# TIMELINE
# --------------------------------------------------
st.subheader("📆 Timeline")

if not df.empty:
    fig = px.timeline(
        df,
        x_start="inicio",
        x_end="fim",
        y="nome",
        color="prioridade"
    )
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)