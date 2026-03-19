from markdownify import markdownify
from bs4 import BeautifulSoup


def convert_html(content: bytes | str, filename: str = "") -> str:
    if isinstance(content, bytes):
        html = content.decode("utf-8", errors="replace")
    else:
        html = content

    # Clean script/style tags first
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    cleaned_html = str(soup)
    md = markdownify(cleaned_html, heading_style="ATX", strip=["img"])
    # Clean up excessive blank lines
    lines = md.split("\n")
    cleaned = []
    blank_count = 0
    for line in lines:
        if line.strip() == "":
            blank_count += 1
            if blank_count <= 2:
                cleaned.append("")
        else:
            blank_count = 0
            cleaned.append(line)

    return "\n".join(cleaned).strip()
