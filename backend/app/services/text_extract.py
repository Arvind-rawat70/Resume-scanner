"""Turn an uploaded file (PDF / DOCX / TXT) into plain text.
Reused by Module 2 for resumes."""
import io
import re
from typing import Tuple

from docx import Document
from pypdf import PdfReader

SUPPORTED = {".pdf", ".docx", ".txt", ".md"}


class UnsupportedFileType(ValueError):
    pass


class EmptyDocument(ValueError):
    pass


def _clean(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\u00a0", " ")
    text = text.replace("\u2022", "•").replace("\uf0b7", "•")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _pdf(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _docx(data: bytes) -> str:
    doc = Document(io.BytesIO(data))
    parts = [p.text for p in doc.paragraphs]
    for table in doc.tables:           # JDs/resumes often hide content in tables
        for row in table.rows:
            parts.append(" | ".join(c.text.strip() for c in row.cells))
    return "\n".join(parts)


def extract_text(filename: str, data: bytes) -> Tuple[str, str]:
    """Returns (text, detected_type)."""
    name = (filename or "").lower()
    ext = name[name.rfind("."):] if "." in name else ""
    if ext == ".pdf":
        text = _pdf(data)
    elif ext == ".docx":
        text = _docx(data)
    elif ext in (".txt", ".md"):
        text = data.decode("utf-8", errors="ignore")
    else:
        raise UnsupportedFileType(
            f"Unsupported file type '{ext or 'unknown'}'. Upload PDF, DOCX or TXT."
        )
    text = _clean(text)
    if len(text) < 30:
        raise EmptyDocument(
            "No readable text found. If this is a scanned PDF, it needs OCR first."
        )
    return text, ext.lstrip(".")
