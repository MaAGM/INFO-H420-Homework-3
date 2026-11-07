"""Centralized configuration, read from environment variables."""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PAPERS_DIR = Path(os.environ.get("PAPERS_DIR", Path.home() / "Google Drive" / "ResearchLibrary" / "papers"))
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", Path.home() / "Google Drive" / "ResearchLibrary" / "output"))
DB_PATH = Path(os.environ.get("DB_PATH", PROJECT_ROOT / "data" / "papers.db"))
MARKDOWN_DIR = Path(os.environ.get("MARKDOWN_DIR", PROJECT_ROOT / "data" / "markdown"))

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")
