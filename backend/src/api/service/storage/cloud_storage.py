# --- Standard Library ---
import json
from pathlib import Path
from typing import List, Tuple, Union
import os

# --- Third-Party ---
import firebase_admin
from firebase_admin import credentials, storage
from google.cloud.exceptions import NotFound
from google.cloud.storage.blob import Blob
from src.api.core import logger

# --- Internal ---
from .base import StorageService
from src.api.core import  logger
from src.api.core.config import get_settings
from src.utils import safe_dir_name
import io
import zipfile
import json
from src.api.service.file_handler.content_type import get_content_type

settings = get_settings()
# Define the credentials
if not settings.FIREBASE_CRED:
    raise ValueError("Firebase Credentials Not Found")


class FireCloudStorageService(StorageService):
    """
    Cloud storage service implementation using Firebase Admin SDK.

    Provides CRUD-like operations for files stored in a Firebase
    (Google Cloud Storage) bucket. Files are organized under a base
    directory (e.g., "questions") and grouped by identifier subdirectories.
    """

    # --- Init / Lifecycle ---

    def __init__(
        self, cred_path: str | Path, bucket_name: str, base_name: str = "questions"
    ):
        """
        Initialize the Firebase Cloud Storage service.

        Args:
            cred_path (str | Path): Path to Firebase service account key JSON.
            bucket_name (str): Name of the Firebase (GCS) bucket.
            base_name (str): Base directory (prefix) for organizing files.
        """
        try:
            if not firebase_admin._apps:
                cred_path = os.path.normpath(cred_path)

                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred, {"storageBucket": bucket_name})
        except Exception as e:
            raise ValueError(f"Could not set up firebase credentials {str(e)}")

        self.bucket = storage.bucket(bucket_name)
        self.base_name: str = base_name

    # --- Directory Management ---
    def get_base_path(self) -> str | Path:
        return self.base_name

    def get_base_name(self) -> str:
        return self.base_name

    def get_storage_path(self, identifier: str) -> Path:
        return Path(self.base_name) / safe_dir_name(identifier)

    def create_storage_path(self, identifier: str) -> Blob:
        blob = self.bucket.blob(self.get_relative_storage_path(identifier))
        blob.upload_from_string("")
        return blob

    def get_relative_storage_path(self, identifier: str) -> str:
        return self.get_storage_path(identifier).as_posix()

    def does_storage_path_exist(self, identifier: str) -> bool:
        target = f"{self.get_relative_storage_path(identifier).rstrip('/')}/"
        logger.debug("Checking if blob exists with target %s", target)
        blobs = list(self.bucket.list_blobs(prefix=target, max_results=1))
        blob = self.bucket.blob(target)
        if blob.exists():
            logger.debug("Found directory marker blob.")
            return True
        return len(blobs) > 0

    # --- File Access ---

    def get_filepath(self, identifier: str, filename: str) -> Path:
        """Return the full path (prefix + identifier + filename)."""
        return self.get_storage_path(identifier) / filename

    def get_blob(self, identifier: str, filename: str) -> Blob:
        """Return a Blob object for the given identifier and filename."""
        file_path = self.get_filepath(identifier, filename)
        return self.bucket.blob(file_path.as_posix())

    def get_file(self, identifier: str, filename: str) -> bytes | None:
        """Download a file as bytes if it exists, else return None."""
        if self.does_file_exist(identifier, filename):
            return self.get_blob(identifier, filename).download_as_bytes()
        return None

    def save_file(
        self,
        identifier: str,
        filename: str,
        content: Union[str, dict, list, bytes, bytearray],
        overwrite: bool = True,
    ) -> Path:
        """
        Save a file to Firebase storage.

        Dicts/lists are serialized as JSON. Bytes/bytearray are decoded.
        """
        blob = self.get_blob(identifier, filename)

        if isinstance(content, (dict, list)):
            content = json.dumps(content, indent=2)
        elif isinstance(content, (bytes, bytearray)):
            content = content.decode()
        elif not isinstance(content, str):
            raise ValueError(f"Unsupported content type: {type(content)}")

        content_type = get_content_type(filename)
        blob.upload_from_string(data=content, content_type=content_type)

        return self.get_filepath(identifier, filename)

    def list_file_names(self, identifier: str) -> List[str]:
        target = self.get_storage_path(identifier).as_posix()
        files: List[str] = []
        for blob in self.bucket.list_blobs(prefix=target):
            logger.debug("Found blob: %s", blob.name)
            relative_path = blob.name[len(target) :]
            if relative_path:
                files.append(relative_path.split("/")[-1])
        return files

    def delete_storage(self, target: str) -> None:
        target = self.get_storage_path(target).as_posix()
        for blob in self.bucket.list_blobs(prefix=target):
            try:
                logger.info("Deleting %s", blob.name)
                blob.delete()
            except NotFound:
                logger.error("Blob not found, nothing to delete.")
        return None

    def delete_file(self, identifier: str, filename: str) -> None:
        """Delete a file if it exists."""
        if self.does_file_exist(identifier, filename):
            self.get_blob(identifier, filename).delete()

    def hard_delete(self) -> None:
        """Delete all files under the base directory prefix."""
        blobs = self.bucket.list_blobs(prefix=str(self.base_name))
        try:
            for blob in blobs:
                logger.info("Deleting %s", blob.name)
                blob.delete()
        except NotFound:
            logger.warning("Base directory not found, nothing to delete.")

    # --- Existence Checks ---

    def does_file_exist(self, identifier: str, filename: str) -> bool:
        """Check if a specific file exists in Firebase storage."""
        return self.get_blob(identifier, filename).exists()

    # --- Download Helpers ---
    # TODO: Make this a function of the filehandler
    async def download_question(self, identifier: str) -> io.BytesIO:
        """Download all files for an identifier as a zipped BytesIO stream."""
        prefix = self.get_storage_path(identifier).as_posix()
        blobs = list(self.bucket.list_blobs(prefix=prefix))

        if not blobs:
            logger.warning("No files to download")
            return io.BytesIO()

        buffer = io.BytesIO()
        manifest: list[dict] = []

        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
            for blob in blobs:
                # strip prefix to avoid double-nested paths
                relative_name = blob.name[len(prefix) :].lstrip("/")
                data = blob.download_as_bytes()
                z.writestr(f"downloads/{identifier}/{relative_name}", data)
                manifest.append({"file": relative_name, "size": len(data)})

            z.writestr(
                "MANIFEST.json",
                json.dumps({"count": len(manifest), "files": manifest}, indent=2),
            )

        buffer.seek(0)
        return buffer
