import os

from minio import Minio
from dotenv import load_dotenv

from fastapi import FastAPI, UploadFile, File

load_dotenv('.env.dev')

app = FastAPI()

minio_client = Minio(
    endpoint=os.getenv('MINIO_ENDPOINT', 'localhost:9000'),
    access_key=os.getenv('MINIO_ACCESS_KEY', 'MINIO_ROOT_USER'),
    secret_key=os.getenv('MINIO_SECRET_KEY', 'MINIO_ROOT_PASSWORD'),
    secure=False,
)


@app.post('/upload')
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()
    size = len(content)

    return {
        'filename': file.filename,
        'content_type': file.content_type,
        'size': size,
    }
