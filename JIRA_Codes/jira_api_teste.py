import requests
from requests.auth import HTTPBasicAuth
import pandas as pd

# Caminho para o certificado raiz confiável da empresa
caminho_certificado = r"claro_.atlassian.net.pem"

# Lê usuário e token do arquivo
with open("jira_api.txt", "r") as file:
    linha = file.readline().strip()
    user1, pwsr1 = linha.split(",")

# Configurações
email = user1
token = pwsr1
dominio_jira = "https://clarobr-jsw-tecnologia.atlassian.net"
projeto = "MTE"  # chave do projeto

# JQL = linguagem de busca do Jira
jql = f"project = {projeto} ORDER BY updated DESC"

url = f"{dominio_jira}/rest/api/3/search"
params = {
    "jql": jql,
    "maxResults": 1000,
    "fields": "summary,status,assignee,created,updated"
}

# Requisição com verificação do certificado customizado
try:
    response = requests.get(
        url,
        headers={"Accept": "application/json"},
        auth=HTTPBasicAuth(email, token),
        params=params,
        verify=caminho_certificado,  # Verificação com seu .pem
        timeout=10
    )
    response.raise_for_status()
except requests.exceptions.RequestException as e:
    print(f"Erro na requisição: {e}")
    print(f"Status: {getattr(e.response, 'status_code', 'sem status')}")
    exit()

# Processar os dados
dados = response.json()
issues = dados.get('issues', [])

# Converter em DataFrame
df = pd.json_normalize(issues)
df.to_excel("kanban_jira.xlsx", index=False)

print("Exportado com sucesso!") 
