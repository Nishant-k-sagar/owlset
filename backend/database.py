import sqlite3
import os
from datetime import datetime

DB_PATH = "data/owlset.db"

class DatabaseManager:
    def __init__(self):
        os.makedirs("data", exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        cursor = self.conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS nodes (
            id TEXT PRIMARY KEY,
            name TEXT,
            type TEXT,
            file_path TEXT,
            start_line INTEGER,
            end_line INTEGER,
            code TEXT,
            docstring TEXT,
            summary TEXT,
            last_updated DATETIME
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS edges (
            source_id TEXT,
            target_id TEXT,
            type TEXT,
            PRIMARY KEY (source_id, target_id, type)
        )
        """)
        self.conn.commit()

    def upsert_node(self, node_data):
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT INTO nodes (id, name, type, file_path, start_line, end_line, code, docstring, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            code=excluded.code,
            start_line=excluded.start_line,
            end_line=excluded.end_line,
            last_updated=excluded.last_updated
        """, (
            node_data['id'], node_data['name'], node_data['type'], 
            node_data['file_path'], node_data['start_line'], node_data['end_line'], 
            node_data['code'], node_data.get('docstring', ''), datetime.now()
        ))
        self.conn.commit()

    def add_edge(self, source, target, edge_type):
        if not source or not target: return
        cursor = self.conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO edges VALUES (?, ?, ?)', (source, target, edge_type))
        self.conn.commit()

    def get_summary(self, node_id):
        cursor = self.conn.cursor()
        res = cursor.execute("SELECT summary FROM nodes WHERE id = ?", (node_id,)).fetchone()
        return res['summary'] if res else None

    def update_summary(self, node_id, summary):
        self.conn.execute("UPDATE nodes SET summary = ? WHERE id = ?", (summary, node_id))
        self.conn.commit()

    def get_all_nodes(self):
        return self.conn.execute("SELECT * FROM nodes").fetchall()

    def get_edges(self):
        return self.conn.execute("SELECT * FROM edges").fetchall()

