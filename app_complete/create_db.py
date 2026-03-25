import sqlite3

with open("init.sql", "r", encoding="utf-8") as f:
    sql_script = f.read()

conn = sqlite3.connect("tarefas.db")
cursor = conn.cursor()
cursor.executescript(sql_script)
conn.commit()
conn.close()

print("✅ Banco criado com sucesso!")