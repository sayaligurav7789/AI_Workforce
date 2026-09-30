from dataclasses import dataclass
from io import BytesIO

from pypdf import PdfReader


class DocumentProcessingError(ValueError):
    pass


@dataclass
class PageText:
    page: int
    text: str


@dataclass
class TextChunk:
    index: int
    page: int
    text: str
    filename: str
    source: str


def extract_pdf_pages(content: bytes) -> list[PageText]:
    if not content.startswith(b"%PDF"):
        raise DocumentProcessingError("The uploaded file is not a valid PDF.")
    try:
        reader = PdfReader(BytesIO(content))
        pages: list[PageText] = []
        for page_number, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if text:
                pages.append(PageText(page=page_number, text=text))
        if not pages:
            raise DocumentProcessingError("The PDF contains no extractable text.")
        return pages
    except DocumentProcessingError:
        raise
    except Exception as exc:
        raise DocumentProcessingError(f"Could not read the PDF: {exc}") from exc


def chunk_pages(pages: list[PageText], filename: str, chunk_size: int = 1400, overlap: int = 220) -> list[TextChunk]:
    chunks: list[TextChunk] = []
    index = 0
    for page in pages:
        text = " ".join(page.text.split())
        start = 0
        while start < len(text):
            end = min(len(text), start + chunk_size)
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(
                    TextChunk(
                        index=index,
                        page=page.page,
                        text=chunk_text,
                        filename=filename,
                        source=f"{filename} page {page.page}",
                    )
                )
                index += 1
            if end >= len(text):
                break
            start = max(end - overlap, start + 1)
    return chunks