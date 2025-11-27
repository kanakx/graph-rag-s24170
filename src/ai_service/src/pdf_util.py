from io import BytesIO
from pypdf import PdfReader


def pdf_to_text(pdf_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(pdf_bytes))
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")

    return "\n\n".join(pages)
