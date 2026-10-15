"""SQLite for local use; persistent PostgreSQL for serverless deployments."""
import sqlite3

class PostgresConnection:
    def __init__(self, url):
        import psycopg
        from psycopg.rows import dict_row
        self.connection=psycopg.connect(url, row_factory=dict_row, connect_timeout=10)
    def execute(self, sql, params=()):
        return self.connection.execute(sql.replace('?', '%s'),params)
    def executemany(self, sql, params):
        return self.connection.cursor().executemany(sql.replace('?', '%s'),params)
    def commit(self): self.connection.commit()
    def rollback(self): self.connection.rollback()
    def close(self): self.connection.close()

def connect(url,path):
    if url: return PostgresConnection(url)
    c=sqlite3.connect(path,timeout=30)
    c.row_factory=sqlite3.Row
    return c

def initialize(c):
    c.execute('CREATE TABLE IF NOT EXISTS documents(id TEXT PRIMARY KEY,name TEXT,format TEXT,bytes BIGINT,created TEXT DEFAULT (CAST(CURRENT_TIMESTAMP AS TEXT)))')
    c.execute('CREATE TABLE IF NOT EXISTS chunks(id TEXT PRIMARY KEY,document_id TEXT REFERENCES documents(id),position INTEGER,text TEXT)')
    c.execute('CREATE INDEX IF NOT EXISTS chunks_document_id ON chunks(document_id)')
