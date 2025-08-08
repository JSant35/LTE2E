import requests
from requests.auth import HTTPBasicAuth
import pandas as pd

# Caminho para o certificado raiz confiável da empresa
caminho_certificado = r"claro_.atlassian.net.pem"

# Leitura das credenciais (arquivo com user,token separados por vírgula)
with open("jira_api.txt", "r") as file:
    user1, pwsr1 = file.readline().strip().split(",")

# Parâmetros de autenticação e API
email = user1
token = pwsr1
dominio_jira = "https://clarobr-jsw-tecnologia.atlassian.net"
projeto = "MTE"

# Montar JQL
jql = f"project = {projeto} ORDER BY updated DESC"

# Campos necessários
fields = "summary,status,assignee,created,updated,subtasks"

# Montar URL e parâmetros
url = f"{dominio_jira}/rest/api/3/search"
params = {
    "jql": jql,
    "maxResults": 1000,
    "fields": fields
}

# Chamada de API
response = requests.get(
    url,
    headers={"Accept": "application/json"},
    auth=HTTPBasicAuth(email, token),
    params=params,
    verify=caminho_certificado,  # ou caminho para o certificado: verify="cert.pem"
    timeout=10
)

# Verifica se a resposta foi bem sucedida
if response.status_code != 200:
    print(f"Erro na requisição: {response.text}")
    exit()

# Processamento dos dados
dados = response.json()
issues = dados['issues']

# Converter em DataFrame
df = pd.json_normalize(issues)

# Verificar subtarefas
df['tem_subtarefas'] = df['fields.subtasks'].apply(
    lambda x: isinstance(x, list) and len(x) > 0
)

# Extrair nomes das subtarefas
def extrair_nomes(subtasks):
    if isinstance(subtasks, list) and subtasks:
        return ", ".join([s.get('fields', {}).get('summary', 'Sem título') for s in subtasks])
    return ""

df['titulos_subtarefas'] = df['fields.subtasks'].apply(extrair_nomes)

# Converter datas removendo timezones
df['created'] = pd.to_datetime(df['fields.created'], errors='coerce').dt.tz_localize(None)
df['updated'] = pd.to_datetime(df['fields.updated'], errors='coerce').dt.tz_localize(None)

# Calcular tempo em dias entre criação e última atualização
df['dias_para_atualizar'] = (df['updated'] - df['created']).dt.days

# Exportar para Excel
df.to_excel("kanban_jira_com_subtarefas.xlsx", index=False)

# Exportar para JSON
df.to_json("kanban_jira_com_subtarefas.json", orient="records", indent=4, force_ascii=False)


print("✅ Exportado com sucesso para 'kanban_jira_com_subtarefas.xlsx'")