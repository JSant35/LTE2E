import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
import os


# Caminho para o certificado
caminho_certificado = r"claro_.atlassian.net.pem"

#folder to export
ffinal_export = "C:\\DSV_APP\\Analytics_DEV\\JIRA_Export\\"

# Garante que a pasta existe
os.makedirs(ffinal_export, exist_ok=True)

# Ler credenciais
with open("jira_api.txt", "r") as file:
    user1, pwsr1 = file.readline().strip().split(",")

# Informações da API
email = user1
token = pwsr1
dominio_jira = "https://clarobr-jsw-tecnologia.atlassian.net"
projeto = "MTE"
fields = "summary,status,assignee,created,updated,subtasks"

# JQL e endpoint
jql = f"project = {projeto} ORDER BY updated DESC"
url = f"{dominio_jira}/rest/api/3/search"
params = {
    "jql": jql,
    "maxResults": 1000,
    "fields": fields
}

# Chamada da API
response = requests.get(
    url,
    headers={"Accept": "application/json"},
    auth=HTTPBasicAuth(email, token),
    params=params,
    verify=caminho_certificado,
    timeout=10
)

if response.status_code != 200:
    print(f"Erro na requisição: {response.text}")
    exit()

issues = response.json()['issues']
dados_completos = []

# Percorrer tarefas principais
for issue in issues:
    pai_key = issue['key']
    pai_summary = issue['fields'].get('summary')
    pai_status = issue['fields'].get('status', {}).get('name')
    pai_created = issue['fields'].get('created')
    pai_updated = issue['fields'].get('updated')
    subtasks = issue['fields'].get('subtasks', [])

    if subtasks:
        for sub in subtasks:
            dados_completos.append({
                "Tarefa_Pai": pai_key,
                "Resumo_Tarefa_Pai": pai_summary,
                "Chave_Tarefa_Pai": pai_key,
                "Criado_Tarefa_Pai": pai_created,
                "Atualizado_Tarefa_Pai": pai_updated,
                "Status_Tarefa_Pai": pai_status,
                "SubTarefa_Key": sub.get('key'),
                "Resumo_SubTarefa": sub.get('fields', {}).get('summary'),
                "Status_SubTarefa": sub.get('fields', {}).get('status', {}).get('name'),
                "Criado_SubTarefa": sub.get('fields', {}).get('created'),
                "Atualizado_SubTarefa": sub.get('fields', {}).get('updated'),
            })
    else:
        dados_completos.append({
            "Tarefa_Pai": pai_key,
            "Resumo_Tarefa_Pai": pai_summary,
            "Chave_Tarefa_Pai": pai_key,
            "Criado_Tarefa_Pai": pai_created,
            "Atualizado_Tarefa_Pai": pai_updated,
            "Status_Tarefa_Pai": pai_status,
            "SubTarefa_Key": None,
            "Resumo_SubTarefa": None,
            "Status_SubTarefa": None,
            "Criado_SubTarefa": None,
            "Atualizado_SubTarefa": None,
        })

# Criar DataFrame
df_final = pd.DataFrame(dados_completos)

# Converter campos de data
for col in ['Criado_Tarefa_Pai', 'Atualizado_Tarefa_Pai', 'Criado_SubTarefa', 'Atualizado_SubTarefa']:
    df_final[col] = pd.to_datetime(df_final[col], errors='coerce').dt.tz_localize(None)

# Calcular tempo de atualização (dias)
df_final['Dias_para_Atualizar_Pai'] = (df_final['Atualizado_Tarefa_Pai'] - df_final['Criado_Tarefa_Pai']).dt.days

# Calcular tempo de atualização da subtarefa, se existir
df_final['Dias_para_Atualizar_Sub'] = (df_final['Atualizado_SubTarefa'] - df_final['Criado_SubTarefa']).dt.days

# Exportar para Excel
# df_final.to_excel("kanban_jira_completo.xlsx", index=False)

# Exportar para JSON
# df_final.to_json("kanban_jira_completo.json", orient="records", indent=4, force_ascii=False)


# Monta caminho completo do arquivo
caminho_excel = os.path.join(ffinal_export, "kanban_jira_completo.xlsx")
caminho_json  = os.path.join(ffinal_export, "kanban_jira_completo.json")

# Exporta para Excel
df_final.to_excel(caminho_excel, index=False)
df_final.to_json(caminho_json, index=False)


print("✅ Exportado com análise de tempo para Excel e JSON com sucesso!")
