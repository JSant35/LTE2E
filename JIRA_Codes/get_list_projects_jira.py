import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
import os

# Caminho do certificado raiz confiável
caminho_certificado = r"C:\DSV_APP\Analytics_DEV\secrets\claro_.atlassian.net.pem"

# Leitura das credenciais (email e token separados por vírgula)
with open(r"C:\DSV_APP\Analytics_DEV\secrets\jira_api.txt", "r") as file:
    user1, pwsr1 = file.readline().strip().split(",")

# Autenticação e domínio
email = user1
token = pwsr1
dominio_jira = "https://clarobr-jsw-tecnologia.atlassian.net"

# URL para listar projetos
url_proj = f"{dominio_jira}/rest/api/3/project"

# Requisição à API
response_proj = requests.get(
    url_proj,
    headers={"Accept": "application/json"},
    auth=HTTPBasicAuth(email, token),
    verify=caminho_certificado,
    timeout=10
)

#folder to export
ffinal_export = "C:\\DSV_APP\\Analytics_DEV\\JIRA_Export\\"

# Monta caminho completo do arquivo
caminho_excel = os.path.join(ffinal_export, "projetos_disponiveis_jira.xlsx")
# caminho_json  = os.path.join(ffinal_export, ".json")


# Verificação da resposta
if response_proj.status_code == 200:
    projetos = response_proj.json()

    # Criar lista com nome e código do projeto
    lista_proj = []
    for p in projetos:
        lista_proj.append({
            "codigo_projeto": p.get("key"),
            "nome_projeto": p.get("name"),
            "tipo_projeto": p.get("projectTypeKey"),
            "id": p.get("id")
        })

    # Converter para DataFrame e exportar
    df_proj = pd.DataFrame(lista_proj)
    df_proj.sort_values(by="nome_projeto", inplace=True)
    df_proj.to_excel(caminho_excel, index=False)
    print("✅ Lista de projetos exportada para 'projetos_disponiveis_jira.xlsx'")

else:
    print(f"❌ Erro ao listar projetos: {response_proj.text}")
