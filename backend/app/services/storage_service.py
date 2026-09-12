import io
from pathlib import Path
from typing import BinaryIO

import boto3

from app.config.settings import settings


class StorageService:
    def __init__(self) -> None:
        self.local_root = Path(settings.LOCAL_STORAGE_PATH)
        if not self.local_root.is_absolute():
            self.local_root = Path(__file__).resolve().parents[2] / self.local_root
        if settings.STORAGE_BACKEND == "local":
            self.local_root.mkdir(parents=True, exist_ok=True)
        self.client = None
        if settings.STORAGE_BACKEND == "s3":
            self.client = boto3.client(
                "s3",
                endpoint_url=settings.STORAGE_ENDPOINT or None,
                aws_access_key_id=settings.STORAGE_ACCESS_KEY,
                aws_secret_access_key=settings.STORAGE_SECRET_KEY,
                region_name=settings.STORAGE_REGION,
            )

    def put(self, key: str, file_obj: BinaryIO, content_type: str) -> None:
        if self.client:
            self.client.upload_fileobj(file_obj, settings.STORAGE_BUCKET, key, ExtraArgs={"ContentType": content_type})
            return
        destination = self.local_root / key
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("wb") as destination_file:
            while chunk := file_obj.read(1024 * 1024):
                destination_file.write(chunk)

    def open(self, key: str) -> BinaryIO:
        if self.client:
            return io.BytesIO(self.client.get_object(Bucket=settings.STORAGE_BUCKET, Key=key)["Body"].read())
        return (self.local_root / key).open("rb")

    def delete(self, key: str) -> None:
        if self.client:
            self.client.delete_object(Bucket=settings.STORAGE_BUCKET, Key=key)
            return
        path = self.local_root / key
        if path.exists():
            path.unlink()


storage = StorageService()