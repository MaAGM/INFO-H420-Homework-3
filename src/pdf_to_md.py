""" Convert a PDF to Markdown with PyMuPDF4LLM. """
from pathlib import Path

import pymupdf4llm


def convert_pdf_to_markdown(pdf_path: str, markdown_dir: str) -> str:
    """ Convert `pdf_path` to Markdown, write it to `markdown_dir`, and return the path of the .md file."""
    pdf = Path(pdf_path)
    out_dir = Path(markdown_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    markdown = pymupdf4llm.to_markdown(str(pdf))
    if not markdown.strip():
        raise ValueError(f"No text extracted from {pdf.name} (PDF scanned ?)")

    md_path = out_dir / f"{pdf.stem}.md"
    md_path.write_text(markdown, encoding="utf-8")
    return str(md_path)
