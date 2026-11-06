import sqlite3
import os

DB_PATH = "data/papers.db"

def init_db():
    """Initialise la base de données et crée la table si elle n'existe pas."""
    # S'assurer que le dossier data/ existe
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            abstract TEXT,
            keywords TEXT,
            category TEXT,
            pdf_path TEXT,
            md_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()