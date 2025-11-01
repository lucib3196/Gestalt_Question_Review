# --- Standard Library ---
from pathlib import Path
from typing import IO, List, Optional

# --- Third-Party ---
from firebase_admin import storage
from google.cloud.exceptions import NotFound
from google.cloud.storage.blob import Blob

# --- Local Modules ---
from src.api.core.logging import logger
from src.api.service.storage.base import StorageService


class FirebaseStorage(StorageService):
    def __init__(self, bucket, base_path):
        logger.info("[Firebase]: Intializing firebase storage ")
        self.bucket = storage.bucket(bucket)
        self.base_path = base_path

    def get_base_path(self) -> str | Path:
        return Path(self.base_path).as_posix()

    def get_storage_path(self, destination: str) -> str:
        return (Path(self.base_path) / destination).as_posix()

    def create_storage_path(self, destination: str) -> Blob:
        target_blob = self.get_storage_path(destination)
        blob: Blob = self.bucket.blob(target_blob)
        blob.upload_from_string("")
        return blob

    def does_storage_path_exist(self, target: str) -> bool:
        target = self.get_storage_path(target)
        blobs = list(self.bucket.list_blobs(prefix=target, max_results=1))
        blob = self.bucket.blob(target)
        if blob.exists():
            return True
        return len(blobs) > 0

    def get_filepath(self, target_path: str, filename: str | None = None) -> str:
        target = self.get_storage_path(target_path)
        if filename:
            target = (Path(target) / filename).as_posix()
        return target

    def upload_file(
        self,
        file_obj: IO[bytes],
        target_path: str,
        filename: str | None = None,
        content_type: str = "application/octet-stream",
    ) -> Blob:
        destination_blob = self.get_filepath(target_path, filename)
        blob = self.bucket.blob(destination_blob)
        if isinstance(file_obj, bytes):
            blob.upload_from_string(file_obj, content_type=content_type)
        else:
            try:
                file_obj.seek(0)
            except Exception:
                pass  # not all IO objects support seek
        blob.upload_from_file(file_obj, content_type=content_type)
        return blob

    def does_file_exist(self, target_path: str, filename: str):
        return self.get_blob(target_path, filename).exists()

    def get_file(self, target: str, filename: Optional[str] = None) -> bytes | None:
        return self.get_blob(target, filename).download_as_bytes()

    def get_blob(self, blob_name: str, filename: Optional[str] = None) -> Blob:
        if not filename:
            return self.bucket.blob(blob_name)
        return self.bucket.blob(self.get_filepath(blob_name, filename))

    def list_files(self, target: str) -> List[str]:
        target = Path(self.get_storage_path(target)).as_posix()
        blobs = self.bucket.list_blobs(prefix=target)
        return [b.name for b in blobs]

    def delete_storage(self, target: str) -> None:
        target = Path(self.get_storage_path(target)).as_posix()
        for blob in self.bucket.list_blobs(prefix=target):
            try:
                logger.info("Deleting %s", blob.name)
                blob.delete()
            except NotFound:
                logger.error("Blob not found, nothing to delete.")
        return None

    def hard_delete(self):
        blobs = self.bucket.list_blobs(prefix=str(self.base_path))
        try:
            for blob in blobs:
                logger.info("Deleting %s", blob.name)
                blob.delete()
        except NotFound:
            logger.warning("Base directory not found, nothing to delete.")
