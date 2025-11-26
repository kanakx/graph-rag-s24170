import io
from uuid import uuid4

from minio import Minio

# from src.file_service.src.file_info import FileInfo
from src.file_info import FileInfo


class MinioFileStorage:
    def __init__(self, client: Minio, bucket_name: str):
        self.client = client
        self.bucket_name = bucket_name

        if not self.client.bucket_exists(bucket_name=self.bucket_name):
            self.client.make_bucket(bucket_name=self.bucket_name)

    def _make_download_url(self, object_name: str) -> str:
        return self.client.presigned_get_object(
            bucket_name=self.bucket_name,
            object_name=object_name,
        )

    def upload(self, content: bytes, content_type: str | None) -> FileInfo:
        file_id = str(uuid4())
        object_name = file_id

        file_bytes = io.BytesIO(content)
        size = len(content)

        self.client.put_object(
            bucket_name=self.bucket_name,
            object_name=object_name,
            data=file_bytes,
            length=size,
            content_type=content_type or "application/octet-stream",
        )

        return FileInfo(
            id=file_id,
            download_url=self._make_download_url(object_name),
        )

    def get(self, file_id: str) -> FileInfo:
        object_name = file_id

        return FileInfo(
            id=file_id,
            download_url=self._make_download_url(object_name),
        )

    def delete(self, file_id: str) -> None:
        object_name = file_id
        self.client.remove_object(
            bucket_name=self.bucket_name,
            object_name=object_name,
        )
