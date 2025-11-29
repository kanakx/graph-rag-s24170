import os

from fastapi import FastAPI
import requests

from .file_info import FileInfo
from .graph_transformer import ingest_cv_text_into_graph
from .pdf_util import pdf_to_text

FILE_SERVICE_URL = os.getenv('FILE_SERVICE_URL')

app = FastAPI()


@app.post("/ingest")
def ingest(request_body: FileInfo):
    file_id = request_body.id
    download_url = request_body.download_url

    pdf_resp = requests.get(download_url, timeout=10.0)
    pdf_resp.raise_for_status()
    pdf_bytes = pdf_resp.content

    text = pdf_to_text(pdf_bytes)
    print(text)

    ingest_cv_text_into_graph(text, source_id=file_id)

    return {"status": "ok"}
