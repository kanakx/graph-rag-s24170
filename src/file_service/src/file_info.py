from pydantic import BaseModel


class FileInfo(BaseModel):
    id: str
    download_url: str
