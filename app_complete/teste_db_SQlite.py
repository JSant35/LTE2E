import sqlite3

conn = sqlite3.connect("tarefas.db")
print(conn.execute("SELECT name FROM sqlite_master").fetchall())