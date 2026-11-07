"""DAG Airflow : PDF of research -> Markdown -> LLM -> SQLite -> HTML -> Discord."""
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Make the `src` package importable from the dags/ folder
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:  # Airflow 3
    from airflow.sdk import dag, task
except ImportError:  # Airflow 2.x
    from airflow.decorators import dag, task

from src import config
from src.db_manager import get_all_papers, get_known_filenames, init_db, save_paper
from src.discord_notifier import notify_paper_processed
from src.html_generator import generate_html
from src.llm import extract_metadata
from src.pdf_to_md import convert_pdf_to_markdown


@dag(
    dag_id="paper_pipeline",
    schedule=timedelta(minutes=10),
    start_date=datetime(2026, 11, 1),
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 1, "retry_delay": timedelta(seconds=30)},
    tags=["info-h420", "research-library"],
)
def paper_pipeline():

    @task
    def find_new_pdfs() -> list[str]:
        """List the PDFs in the papers/ folder that are not in the database."""
        init_db(str(config.DB_PATH))
        known = get_known_filenames(str(config.DB_PATH))
        pdfs = sorted(p for p in Path(config.PAPERS_DIR).glob("*.pdf") if p.name not in known)
        return [str(p) for p in pdfs]

    @task
    def convert_pdf(pdf_path: str) -> dict:
        md_path = convert_pdf_to_markdown(pdf_path, str(config.MARKDOWN_DIR))
        return {"filename": Path(pdf_path).name, "markdown_path": md_path}

    @task
    def generate_metadata(converted: dict) -> dict:
        markdown = Path(converted["markdown_path"]).read_text(encoding="utf-8")
        metadata = extract_metadata(markdown, config.OLLAMA_BASE_URL, config.OLLAMA_MODEL)
        return {"filename": converted["filename"], **metadata}

    @task
    def store_paper(record: dict) -> dict:
        save_paper(
            str(config.DB_PATH), record["filename"], record["title"],
            record["summary"], record["keywords"], record["category"],
        )
        return record

    @task
    def regenerate_html(stored: list[dict]) -> str:
        """Regenerate index.html from the entire database (the parameter is for dependency)."""
        papers = get_all_papers(str(config.DB_PATH))
        return generate_html(papers, str(Path(config.OUTPUT_DIR) / "index.html"))

    @task
    def send_notification(record: dict) -> None:
        notify_paper_processed(
            config.DISCORD_WEBHOOK_URL, record["title"], record["category"],
            record["filename"], record["summary"],
        )

    new_pdfs = find_new_pdfs()
    converted = convert_pdf.expand(pdf_path=new_pdfs)
    metadata = generate_metadata.expand(converted=converted)
    stored = store_paper.expand(record=metadata)
    html_done = regenerate_html(stored)
    notifications = send_notification.expand(record=stored)
    html_done >> notifications  # Only notify once the page is up to date


paper_pipeline()
