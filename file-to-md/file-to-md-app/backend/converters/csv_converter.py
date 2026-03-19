import csv
import io


def convert_csv(content: bytes, filename: str = "") -> str:
    text = content.decode("utf-8", errors="replace")
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)

    if not rows:
        return ""

    headers = rows[0]
    md_lines = []

    # Header row
    md_lines.append("| " + " | ".join(headers) + " |")
    # Separator
    md_lines.append("| " + " | ".join("---" for _ in headers) + " |")
    # Data rows
    for row in rows[1:]:
        # Pad row if shorter than headers
        padded = row + [""] * (len(headers) - len(row))
        md_lines.append("| " + " | ".join(padded[: len(headers)]) + " |")

    return "\n".join(md_lines)
