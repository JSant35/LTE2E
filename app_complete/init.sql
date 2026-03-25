-- =============================================
-- TASK MASTER PRO – BANCO DE DADOS SQLITE
-- =============================================

-- -----------------------------
-- TABELA DE USUÁRIOS
-- -----------------------------
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT UNIQUE NOT NULL,
    senha BLOB NOT NULL
);

-- -----------------------------
-- TABELA DE TAREFAS
-- -----------------------------
CREATE TABLE IF NOT EXISTS tarefas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
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
    id_usuario INTEGER NOT NULL,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id)
);

-- -----------------------------
-- TABELA DE SUBTAREFAS
-- -----------------------------
CREATE TABLE IF NOT EXISTS subtarefas (
    id_sub INTEGER PRIMARY KEY AUTOINCREMENT,
    id_tarefa INTEGER NOT NULL,
    nome TEXT NOT NULL,
    status TEXT,
    FOREIGN KEY (id_tarefa) REFERENCES tarefas(id)
);