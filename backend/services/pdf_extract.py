"""Extract text from uploaded files (PDFs and plain text)."""
from __future__ import annotations

import os
from typing import Optional


def extract_text(path: str) -> str:
    """Best-effort text extraction. Returns empty string on failure."""
    if not os.path.isfile(path):
        return ""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return _extract_pdf(path)
    if ext in {".txt", ".md", ".markdown"}:
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except OSError:
            return ""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            data = f.read()
        return data
    except OSError:
        return ""


def _extract_pdf(path: str) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        return ""
    try:
        reader = PdfReader(path)
    except Exception:
        return ""

    chunks = []
    for page in reader.pages:
        text = ""
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        if not text.strip():
            try:
                text = page.extract_text(extraction_mode="layout") or ""
            except Exception:
                pass
        if text.strip():
            chunks.append(text)
    return "\n\n".join(chunks)


def write_text_cache(text_path: str, text: str) -> None:
    try:
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(text)
    except OSError:
        pass


def read_text_cache(text_path: str) -> Optional[str]:
    if not os.path.isfile(text_path):
        return None
    try:
        with open(text_path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None
