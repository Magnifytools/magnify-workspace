import io
from PIL import Image
import pytesseract


def convert_image(content: bytes, filename: str = "") -> str:
    image = Image.open(io.BytesIO(content))

    # Try Spanish + English OCR
    try:
        text = pytesseract.image_to_string(image, lang="spa+eng")
    except pytesseract.TesseractError:
        # Fallback to English only
        text = pytesseract.image_to_string(image, lang="eng")

    text = text.strip()
    if not text:
        return "*No se pudo extraer texto de la imagen.*"

    return text
