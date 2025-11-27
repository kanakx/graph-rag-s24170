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

    # 1) Download PDF directly
    pdf_resp = requests.get(download_url, timeout=10.0)
    pdf_resp.raise_for_status()
    pdf_bytes = pdf_resp.content

    # 2) Extract text
    text = pdf_to_text(pdf_bytes)
    print(text)

    # 3) Text -> graph in Neo4j (LLMGraphTransformer)
    ingest_cv_text_into_graph(text, source_id=file_id)

    return {"status": "ok"}
