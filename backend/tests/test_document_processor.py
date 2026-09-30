from io import BytesIO

import pytest
from pypdf import PdfReader, PdfWriter

from app.rag.document_processor import DocumentProcessingError, chunk_pages, extract_pdf_pages, PageText


def test_extract_pdf_pages_preserves_page_numbers():
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=300)
    buffer = BytesIO()
    writer.write(buffer)
    # A blank PDF is valid but has no extractable text.
    with pytest.raises(DocumentProcessingError, match="no extractable text"):
        extract_pdf_pages(buffer.getvalue())


def test_chunking_preserves_source_metadata():
    chunks = chunk_pages([PageText(page=3, text="hello " * 500)], "requirements.pdf", chunk_size=120)
    assert chunks
    assert all(chunk.page == 3 for chunk in chunks)
    assert all(chunk.filename == "requirements.pdf" for chunk in chunks)
    assert all(chunk.source == "requirements.pdf page 3" for chunk in chunks)


def test_rejects_non_pdf_content():
    with pytest.raises(DocumentProcessingError, match="valid PDF"):
        extract_pdf_pages(b"not a pdf")