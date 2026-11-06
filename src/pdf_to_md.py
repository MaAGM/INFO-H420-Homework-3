"""Conversion d'un PDF en Markdown avec PyMuPDF4LLM."""
from pathlib import Path

import pymupdf4llm


def convert_pdf_to_markdown(pdf_path: str, markdown_dir: str) -> str:
    """Convertit `pdf_path` en Markdown, l'écrit dans `markdown_dir` et renvoie le chemin du .md."""
    pdf = Path(pdf_path)
    out_dir = Path(markdown_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    markdown = pymupdf4llm.to_markdown(str(pdf))
    if not markdown.strip():
        raise ValueError(f"Aucun texte extrait de {pdf.name} (PDF scanné ?)")

    md_path = out_dir / f"{pdf.stem}.md"
    md_path.write_text(markdown, encoding="utf-8")
    return str(md_path)
