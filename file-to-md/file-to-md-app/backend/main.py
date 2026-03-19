import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests as http_requests

from converters import (
    convert_pdf,
    convert_docx,
    convert_image,
    convert_html,
    convert_csv,
    convert_txt,
)

app = FastAPI(title="File to Markdown Converter")

cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:5177,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

CONVERTERS = {
    ".pdf": convert_pdf,
    ".docx": convert_docx,
    ".png": convert_image,
    ".jpg": convert_image,
    ".jpeg": convert_image,
    ".webp": convert_image,
    ".html": convert_html,
    ".htm": convert_html,
    ".txt": convert_txt,
    ".csv": convert_csv,
}

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


class UrlRequest(BaseModel):
    url: str


class BulkUrlRequest(BaseModel):
    urls: list[str]


class HtmlRequest(BaseModel):
    html: str


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/convert/file")
async def convert_file(file: UploadFile = File(...)):
    filename = file.filename or "file.txt"
    ext = os.path.splitext(filename)[1].lower()

    if ext not in CONVERTERS:
        raise HTTPException(
            status_code=422,
            detail=f"Tipo de archivo no soportado: {ext}. Soportados: {', '.join(CONVERTERS.keys())}",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="El archivo excede el límite de 20MB.")

    try:
        markdown = CONVERTERS[ext](content, filename)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Error al procesar {filename}: {str(e)}",
        )

    return {"markdown": markdown, "filename": filename}


@app.post("/api/convert/url")
def convert_url(req: UrlRequest):
    url = req.url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        resp = http_requests.get(
            url,
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0 (compatible; FileToMD/1.0)"},
        )
        resp.raise_for_status()
    except http_requests.RequestException as e:
        raise HTTPException(status_code=422, detail=f"No se pudo obtener la URL: {str(e)}")

    try:
        markdown = convert_html(resp.text)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Error al convertir HTML: {str(e)}")

    return {"markdown": markdown, "source_url": url}


@app.post("/api/convert/urls")
def convert_urls_bulk(req: BulkUrlRequest):
    results = []
    for raw_url in req.urls:
        url = raw_url.strip()
        if not url:
            continue
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:
            resp = http_requests.get(
                url,
                timeout=15,
                headers={"User-Agent": "Mozilla/5.0 (compatible; FileToMD/1.0)"},
            )
            resp.raise_for_status()
            md = convert_html(resp.text)
            results.append({"url": url, "markdown": md, "error": None})
        except Exception as e:
            results.append({"url": url, "markdown": "", "error": str(e)})

    return {"results": results}


@app.post("/api/convert/html")
def convert_html_paste(req: HtmlRequest):
    if not req.html.strip():
        raise HTTPException(status_code=422, detail="El HTML está vacío.")

    try:
        markdown = convert_html(req.html)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Error al convertir HTML: {str(e)}")

    return {"markdown": markdown}


# --- Serve frontend static files in production ---
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.isdir(static_dir):
    from fastapi.staticfiles import StaticFiles
    from starlette.responses import FileResponse

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = os.path.join(static_dir, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(static_dir, "index.html"))
