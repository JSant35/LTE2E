Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "     SETUP DO BANCO - TASK MASTER PRO     " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Caminhos
$sqlitePath = ".\sqlite\sqlite3.exe"
$sqlFile = "init.sql"
$dbFile = "tarefas.db"

# -----------------------------
# Verificar sqlite3.exe
# -----------------------------
if (-Not (Test-Path $sqlitePath)) {
    Write-Host "ERRO: sqlite3.exe não encontrado em ./sqlite/" -ForegroundColor Red
    exit
}
Write-Host "✅ sqlite3.exe encontrado." -ForegroundColor Green

# -----------------------------
# Verificar init.sql
# -----------------------------
if (-Not (Test-Path $sqlFile)) {
    Write-Host "ERRO: init.sql não encontrado." -ForegroundColor Red
    exit
}
Write-Host "✅ init.sql encontrado." -ForegroundColor Green

# -----------------------------
# Criar banco se não existir
# -----------------------------
if (-Not (Test-Path $dbFile)) {
    Write-Host "📄 Criando tarefas.db..." -ForegroundColor Yellow
    New-Item $dbFile -ItemType File | Out-Null
} else {
    Write-Host "ℹ️ Banco já existe. Continuando..." -ForegroundColor Yellow
}

# -----------------------------
# Executar init.sql corretamente
# -----------------------------
Write-Host "📌 Executando script init.sql..." -ForegroundColor Yellow

Start-Process `
    -FilePath $sqlitePath `
    -ArgumentList @("$dbFile", ".read `"$sqlFile`"") `
    -Wait `
    -NoNewWindow

Write-Host "✅ Estrutura criada/atualizada!" -ForegroundColor Green

# -----------------------------
# Mostrar tabelas criadas
# -----------------------------
Write-Host ""
Write-Host "📊 Tabelas existentes:" -ForegroundColor Cyan

Start-Process `
    -FilePath $sqlitePath `
    -ArgumentList @("$dbFile", ".tables") `
    -Wait `
    -NoNewWindow

Write-Host ""
Write-Host "✅ SETUP FINALIZADO!"
Write-Host "Execute o app com: streamlit run app_complete.py" -ForegroundColor Green