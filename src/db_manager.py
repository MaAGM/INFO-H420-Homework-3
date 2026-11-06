"""Gestion de la base SQLite locale (hors du dossier synchronisé)."""
import json
import sqlite3
from contextlib import closing
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS papers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    keywords TEXT NOT NULL,
    category TEXT NOT NULL
)
"""


def _connect(db_path: str) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str) -> None:
    with closing(_connect(db_path)) as conn, conn:
        conn.execute(SCHEMA)


def get_known_filenames(db_path: str) -> set[str]:
    init_db(db_path)
    with closing(_connect(db_path)) as conn:
        return {row["filename"] for row in conn.execute("SELECT filename FROM papers")}


def save_paper(db_path: str, filename: str, title: str, summary: str,
               keywords: list[str], category: str) -> None:
    """Insère ou met à jour (selon `filename`) une fiche d'article."""
    init_db(db_path)
    with closing(_connect(db_path)) as conn, conn:
        conn.execute(
            """INSERT INTO papers (filename, title, summary, keywords, category)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(filename) DO UPDATE SET
                   title=excluded.title, summary=excluded.summary,
                   keywords=excluded.keywords, category=excluded.category""",
            (filename, title, summary, json.dumps(keywords, ensure_ascii=False), category),
        )


def get_all_papers(db_path: str) -> list[dict]:
    init_db(db_path)
    with closing(_connect(db_path)) as conn:
        rows = conn.execute(
            "SELECT filename, title, summary, keywords, category FROM papers ORDER BY title COLLATE NOCASE"
        ).fetchall()
    papers = []
    for row in rows:
        paper = dict(row)
        paper["keywords"] = json.loads(paper["keywords"])
        papers.append(paper)
    return papers
