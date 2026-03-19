def convert_txt(content: bytes, filename: str = "") -> str:
    text = content.decode("utf-8", errors="replace")
    return text
