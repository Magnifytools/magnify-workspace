import io
import fitz  # PyMuPDF


def convert_pdf(content: bytes, filename: str = "") -> str:
    doc = fitz.open(stream=content, filetype="pdf")
    pages = []

    for i, page in enumerate(doc):
        text = page.get_text().strip()
        if text:
            pages.append(f"## Página {i + 1}\n\n{text}")

    doc.close()
    return "\n\n---\n\n".join(pages) if pages else "*El PDF no contiene texto extraíble.*"
