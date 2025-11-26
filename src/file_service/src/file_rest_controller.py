import os

from fastapi import FastAPI, UploadFile, File, HTTPException
from minio import Minio
from minio.error import S3Error

from .file_info import FileInfo
from .minio_file_storage import MinioFileStorage

MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT')
MINIO_ACCESS_KEY = os.getenv('MINIO_ROOT_USER')
MINIO_SECRET_KEY = os.getenv('MINIO_ROOT_PASSWORD')
MINIO_BUCKET_NAME = os.getenv('MINIO_BUCKET_NAME')
MINIO_SECURE = os.getenv('MINIO_SECURE', 'False').lower() == 'true'

app = FastAPI()

minio_client = Minio(
    endpoint=MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=bool(MINIO_SECURE),
)

storage = MinioFileStorage(minio_client, MINIO_BUCKET_NAME)


def make_download_url(object_name: str) -> str:
    return minio_client.presigned_get_object(
        bucket_name=MINIO_BUCKET_NAME,
        object_name=object_name,
    )


@app.on_event('startup')
def ensure_bucket_exists():
    if not minio_client.bucket_exists(bucket_name=MINIO_BUCKET_NAME):
        minio_client.make_bucket(bucket_name=MINIO_BUCKET_NAME)


@app.post("/files", response_model=FileInfo)
async def upload_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        return storage.upload(content, file.content_type)
    except S3Error as e:
        raise HTTPException(status_code=500, detail=f"MinIO error: {e}")


@app.get("/files/{file_id}", response_model=FileInfo)
def get_file(file_id: str):
    object_name = file_id
    try:
        minio_client.stat_object(bucket_name=MINIO_BUCKET_NAME, object_name=object_name)
    except S3Error as e:
        if e.code in {"NoSuchKey", "NoSuchObject"}:
            raise HTTPException(status_code=404, detail="File not found")
        raise HTTPException(status_code=500, detail=f"MinIO error: {e}")

    return FileInfo(id=file_id, download_url=make_download_url(object_name))


@app.delete("/files/{file_id}", status_code=204)
def delete_file(file_id: str):
    object_name = file_id
    try:
        minio_client.remove_object(bucket_name=MINIO_BUCKET_NAME, object_name=object_name)
    except S3Error as e:
        if e.code in {"NoSuchKey", "NoSuchObject"}:
            raise HTTPException(status_code=404, detail="File not found")
        raise HTTPException(status_code=500, detail=f"MinIO error: {e}")
