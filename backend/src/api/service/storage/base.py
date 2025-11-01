from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union, Optional, List
from google.cloud.storage.blob import Blob
import io
from typing import IO, Optional, Annotated


class StorageService:
    """
    Base storage interface for managing files and directories.

    This abstract class defines the core methods required for any storage backend.
    Subclasses should implement these methods based on the underlying storage mechanism
    (e.g., local filesystem, cloud bucket, or hybrid configuration).
    """

    # -------------------------------------------------------------------------
    # Base path and metadata
    # -------------------------------------------------------------------------
    def get_base_path(self) -> Union[str, Path]:
        """
        Return the absolute path (or URI) to the base storage directory or bucket.

        Returns
        -------
        Union[str, Path]
            The absolute path or URI where resources are stored.
        """
        raise NotImplementedError("get_base_path must be implemented by subclass")


    # -------------------------------------------------------------------------
    # Storage path operations
    # -------------------------------------------------------------------------
    def get_storage_path(self, destination: str) -> str:
        """
        Return the absolute path to the directory for a given resource identifier.

        Parameters
        ----------
        identifier : str
            The unique name or ID of the stored resource.

        Returns
        -------
        Path
            The directory path corresponding to the given identifier.
        """
        raise NotImplementedError("get_storage_path must be implemented by subclass")

    def create_storage_path(self, destination: str) -> Path | Blob:
        """
        Create a new directory or container for the given resource identifier.

        Parameters
        ----------
        identifier : str
            The unique name or ID of the resource.

        Returns
        -------
        Path
            The created directory path.
        """
        raise NotImplementedError("create_storage_path must be implemented by subclass")

    def get_relative_storage_path(self, identifier: str) -> str | Path:
        """
        Return the relative path (from the base directory) for the given identifier.

        Parameters
        ----------
        identifier : str
            The unique name or ID of the resource.

        Returns
        -------
        Path
            The relative path to the resource directory.
        """
        raise NotImplementedError(
            "get_relative_storage_path must be implemented by subclass"
        )

    def does_storage_path_exist(self, target: str) -> bool:
        """
        Check whether a storage directory or container exists for the given identifier.

        Parameters
        ----------
        identifier : str
            The unique name or ID of the resource.

        Returns
        -------
        bool
            True if the path exists, False otherwise.
        """
        raise NotImplementedError(
            "does_storage_path_exist must be implemented by subclass"
        )

    # -------------------------------------------------------------------------
    # File operations
    # -------------------------------------------------------------------------
    def get_file(self, target: str, filename: Optional[str] = None) -> Optional[bytes]:
        """
        Retrieve the raw contents of a file for a given identifier.

        Parameters
        ----------
        identifier : str
            The resource identifier.
        filename : str
            The name of the file to retrieve.

        Returns
        -------
        Optional[bytes]
            The file contents as bytes, or None if the file does not exist.
        """
        raise NotImplementedError("get_file must be implemented by subclass")

    def get_filepath(self, target_path: str, filename: Optional[str] = None) -> str:
        """
        Return the absolute path to a specific file inside an identifier directory.

        Parameters
        ----------
        identifier : str
            The resource identifier.
        filename : str
            The file name within that resource's directory.

        Returns
        -------
        Path
            The absolute path to the requested file.
        """
        raise NotImplementedError("get_filepath must be implemented by subclass")

    def upload_file(
        self,
        file_obj: IO[bytes],
        target_path: str,
        filename: Optional[str] = None,
        content_type: str = "application/octet-stream",
    ) -> Blob | Path:
        raise NotImplementedError(
            "Upload file must be implemented by base storage class"
        )

    def save_file(
        self,
        identifier: str,
        filename: str,
        content: Union[str, dict, list, bytes, bytearray],
        overwrite: bool = True,
    ) -> Path:
        """
        Save a file under the given identifier directory.

        Parameters
        ----------
        identifier : str
            The resource identifier.
        filename : str
            The target filename.
        content : Union[str, dict, list, bytes, bytearray]
            The file content to be saved.
        overwrite : bool, default=True
            Whether to overwrite an existing file with the same name.

        Returns
        -------
        Path
            The absolute path of the saved file.
        """
        raise NotImplementedError("save_file must be implemented by subclass")

    def list_files(self, target: str) -> List[str]:
        """
        List all file names under a given identifier directory.

        Parameters
        ----------
        identifier : str
            The resource identifier.

        Returns
        -------
        List[str]
            A list of file names within the identifier directory.
        """
        raise NotImplementedError("list_file_names must be implemented by subclass")

    def delete_storage(self, target: str) -> None:
        """
        Delete an entire storage directory or container for the given identifier.

        Parameters
        ----------
        identifier : str
            The resource identifier.
        """
        raise NotImplementedError("delete_storage must be implemented by subclass")

    def delete_file(self, identifier: str, filename: str) -> None:
        """
        Delete a specific file under a given identifier directory.

        Parameters
        ----------
        identifier : str
            The resource identifier.
        filename : str
            The name of the file to delete.
        """
        raise NotImplementedError("delete_file must be implemented by subclass")

    def hard_delete(self):
        raise NotImplementedError("hard_delete must be implemented by subclass")

    # -------------------------------------------------------------------------
    # Async download utilities
    # -------------------------------------------------------------------------
    async def download_question(self, identifier: str) -> bytes | io.BytesIO:
        """
        Download the contents of a single question or resource.

        Parameters
        ----------
        identifier : str
            The unique identifier for the resource.

        Returns
        -------
        bytes | io.BytesIO
            The downloaded file data.
        """
        raise NotImplementedError("download_question must be implemented by subclass")

    async def download_questions(self, identifiers: List[str]) -> None:
        """
        Download multiple questions or resources by their identifiers.

        Parameters
        ----------
        identifiers : List[str]
            A list of unique resource identifiers to download.
        """
        raise NotImplementedError("download_questions must be implemented by subclass")
