import requests
import pandas as pd
from datetime import datetime
import getpass
import json
import os

# Caminho para o certificado
caminho_certificado = r"C:\DSV_APP\Analytics_DEV\secrets\claro_.atlassian.net.pem"

#folder to export
ffinal_export = "C:\\DSV_APP\\Analytics_DEV\\JIRA_Export\\"

# Função para extrair datas do campo description
def extrair_datas_da_description(description):
    data_inicio = ""
    data_fim = ""

    if not isinstance(description, dict):
        return data_inicio, data_fim

    textos = []
    for bloco in description.get("content", []):
        for item in bloco.get("content", []):
            text = item.get("text", "").strip()
            if text:
                textos.append(text)

    # # DEBUG opcional
    # print("📋 Textos encontrados na descrição:")
    # for t in textos:
    #     print("-", t)

    for i, txt in enumerate(textos):
        if "Data do início da mudança" in txt and i + 1 < len(textos):
            data_inicio = textos[i + 1].strip()
        if "Data do fim da mudança" in txt and i + 1 < len(textos):
            data_fim = textos[i + 1].strip()

    return data_inicio, data_fim


# Get API user/token
with open(r"C:\DSV_APP\Analytics_DEV\secrets\jira_api.txt", "r") as file:
    for line in file:
        user1 = line.strip().split(",")[0]
        pwsr1 = line.strip().split(",")[1]

auth = (user1, pwsr1)
headers = {"Accept": "application/json"}

campo_inicio_id = "customfield_17144"
executed_by = getpass.getuser()

# Endpoint e busca
search_url = "https://clarobr.atlassian.net/rest/api/3/search"
params = {
    "jql": "project = GML AND 'gerentes aprovadores[paragraph]' ~ 'Grupo Aprovador: BI-GERENCIA_ANALYTICS(APR) RADAKIAN MAURITY SOUSA LINO WELINGTON DUARTE DE ARAUJO FABIANO RONALDO DIAS' AND textfields ~ 'MOTOR TÉCNICO' ORDER BY created DESC",
    "maxResults": 10
}

resultados = []

response = requests.get(search_url, params=params, headers=headers, auth=auth, verify=caminho_certificado, timeout=30)

if response.status_code == 200:
    issues = response.json().get("issues", [])
    print(f"🔍 {len(issues)} tickets encontrados.\n")

    for issue in issues:
        key = issue['key']
        summary = issue['fields'].get('summary', '')
        print(f"🔹 {key} - {summary}")

        issue_url = f"https://clarobr.atlassian.net/rest/api/3/issue/{key}"
        issue_response = requests.get(issue_url, headers=headers, auth=auth, verify=caminho_certificado, timeout=30)

        if issue_response.status_code == 200:
            issue_data = issue_response.json()
            fields = issue_data.get('fields', {})

            # Campo estruturado de início
            data_inicio = fields.get(campo_inicio_id, "")

            # NOVO: extração das datas do campo description
            description = fields.get("description")
            data_inicio_mudanca, data_fim_mudanca = extrair_datas_da_description(description)

            # Vínculos
            linked_issues = fields.get('issuelinks', [])

            if linked_issues:
                for link in linked_issues:
                    if 'outwardIssue' in link:
                        linked_key = link['outwardIssue']['key']
                        linked_summary = link['outwardIssue']['fields']['summary']
                        link_type = link.get('type', {}).get('name', '')
                    elif 'inwardIssue' in link:
                        linked_key = link['inwardIssue']['key']
                        linked_summary = link['inwardIssue']['fields']['summary']
                        link_type = link.get('type', {}).get('name', '')
                    else:
                        linked_key = linked_summary = link_type = ""

                    resultados.append({
                        "Issue Key": key,
                        "Summary": summary,
                        "Linked Key": linked_key,
                        "Linked Summary": linked_summary,
                        "Link Type": link_type,
                        "Data/Hora Início": data_inicio,
                        "Data Início Mudança": data_inicio_mudanca,
                        "Data Fim Mudança": data_fim_mudanca,
                        "Executado Por": executed_by
                    })
            else:
                resultados.append({
                    "Issue Key": key,
                    "Summary": summary,
                    "Linked Key": "",
                    "Linked Summary": "",
                    "Link Type": "",
                    "Data/Hora Início": data_inicio,
                    "Data Início Mudança": data_inicio_mudanca,
                    "Data Fim Mudança": data_fim_mudanca,
                    "Executado Por": executed_by
                })
        else:
            print(f"⚠️ Erro ao buscar detalhes de {key}: {issue_response.status_code}")
else:
    print(f"❌ Falha na requisição inicial: {response.status_code}")



# Monta caminho completo do arquivo
caminho_excel = os.path.join(ffinal_export, "jira_tickets_com_vinculos.xlsx")
caminho_json = os.path.join(ffinal_export, "jira_tickets_com_vinculos.json")

# Cria DataFrame e converte colunas
df = pd.DataFrame(resultados)
df["Data Início Mudança"] = pd.to_datetime(df["Data Início Mudança"], format="%d/%m/%Y %H:%M", errors="coerce")
df["Data Fim Mudança"] = pd.to_datetime(df["Data Fim Mudança"], format="%d/%m/%Y %H:%M", errors="coerce")
df["Data/Hora Início"] = pd.to_datetime(df["Data/Hora Início"], errors="coerce")

# Exporta
df.to_excel(caminho_excel, index=False)
df.to_json(caminho_json, orient="records", force_ascii=False, indent=2)
print("✅ Exportações finalizadas.")
