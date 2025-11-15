# --- Third-Party ---
from fastapi import APIRouter, HTTPException
from starlette import status
import json
import mimetypes
import base64
from src.utils import encode_image

# --- Internal ---
from src.api.core import logger
from src.api.service.question.question_manager import QuestionManagerDependency
from src.api.service.storage_manager import StorageDependency
from src.api.models import *
from fastapi import UploadFile
from src.api.service.file_service import FileServiceDep
from src.api.models.response_models import FileData
from src.api.dependencies import StorageTypeDep
from fastapi.responses import Response

router = APIRouter(
    prefix="/questions",
    tags=["questions", "files"],
)

CLIENT_FILE_DIR = "clientFiles"
client_file_extensions = {
    ".png",
    ".jpg",
    ".jpeg",
    ".pdf",
}


@router.get("/files/{qid}")
async def get_question_files(
    qid: str | UUID,
    qm: QuestionManagerDependency,
    storage: StorageDependency,
    storage_type: StorageTypeDep,
) -> SuccessFileResponse:
    """
    Retrieve a list of filenames associated with a given question.

    This endpoint locates the question by its unique identifier (UUID or string ID),
    determines the corresponding storage directory, and returns the filenames
    of all available files within that question’s folder.

    Args:
        qid (str | UUID): The unique identifier of the question.
        qm (QuestionManagerDependency): Dependency that manages question retrieval.
        storage (StorageDependency): Dependency that handles file storage operations.

    Returns:
        SuccessFileResponse: A response containing a list of filenames related to the question.

    Raises:
        HTTPException(404): If the question cannot be found.
        HTTPException(500): If the filenames cannot be retrieved due to a server error.
    """
    try:
        question = qm.get_question(qid)
        question_path = qm.get_question_path(question.id, storage_type)
        assert question_path
        files = storage.list_files(question_path)
        return SuccessFileResponse(
            status=200, detail="Retrieved files ok", filenames=files
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not retrieve file names: {e}",
        )


@router.delete("/files/{qid}/{filename}")
async def delete_file(
    qid: str | UUID,
    filename: str,
    qm: QuestionManagerDependency,
    storage: StorageDependency,
    storage_type: StorageTypeDep,
    fm: FileServiceDep,
):
    try:
        question = qm.get_question(qid)
        question_path = Path(qm.get_question_path(question.id, storage_type))
        logger.debug(f"The question path is {question_path}")
        if await fm.is_image(filename):
            filepath = question_path / CLIENT_FILE_DIR / filename
        else:
            filepath = question_path / filename

        resolved_filepath = storage.get_storage_path(filepath, relative=False)
        logger.info("Deleting the resolved file %s", resolved_filepath)
        storage.delete_file(resolved_filepath)
        return SuccessDataResponse(status=200, detail="Deleted file ok")
    except HTTPException:
        raise


@router.get("/files/{qid}/{filename}")
async def read_question_file(
    qid: str | UUID,
    filename: str,
    qm: QuestionManagerDependency,
    storage: StorageDependency,
    storage_type: StorageTypeDep,
) -> SuccessDataResponse:
    """
    Read the contents of a specific file associated with a given question.

    This endpoint retrieves a single file from the question's storage path and
    decodes its contents into a UTF-8 string before returning it in the response.

    Args:
        qid (str | UUID): The unique identifier of the question.
        filename (str): The name of the file to retrieve.
        qm (QuestionManagerDependency): Dependency that manages question retrieval.
        storage (StorageDependency): Dependency that handles file storage operations.

    Returns:
        SuccessDataResponse: A response containing the decoded file contents.

    Raises:
        HTTPException(404): If the question or file cannot be found.
        HTTPException(500): If the file cannot be read or decoded due to a server error.
    """
    try:
        question = qm.get_question(qid)
        question_path = qm.get_question_path(question.id, storage_type)
        data = storage.read_file(question_path, filename)
        if data:
            data = data.decode("utf-8")
        return SuccessDataResponse(
            status=status.HTTP_200_OK, detail=f"Read file {filename} success", data=data
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not read file {filename}: {e}",
        )


# Update
@router.put("/files/{qid}/{filename}")
async def update_file(
    qid: str | UUID,
    filename: str,
    new_content: str | dict,
    qm: QuestionManagerDependency,
    storage: StorageDependency,
    storage_type: StorageTypeDep,
) -> SuccessDataResponse:
    """
    Update or overwrite a file associated with a specific question.

    This endpoint writes new content to an existing file in the question's storage path.
    If the file already exists, its contents are replaced. The `new_content` can be
    provided as a raw string or a dictionary, which will automatically be serialized to JSON.

    Args:
        qid (str | UUID): The unique identifier of the question.
        filename (str): The name of the file to update or overwrite.
        new_content (str | dict): The new content to be written to the file.
        qm (QuestionManagerDependency): Dependency that manages question retrieval.
        storage (StorageDependency): Dependency that handles file storage operations.

    Returns:
        SuccessDataResponse: A response confirming the update and returning the written content.

    Raises:
        HTTPException(404): If the question is not found.
        HTTPException(500): If the file cannot be written due to a server error.
    """
    try:
        if isinstance(new_content, dict):
            new_content = json.dumps(new_content)
        question = qm.get_question(qid)
        question_path = qm.get_question_path(question.id, storage_type)
        assert question_path
        path = storage.save_file(question_path, filename, new_content, overwrite=True)
        return SuccessDataResponse(
            status=200, detail=f"Wrote file successfully to {path}", data=new_content
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not write file content: {e}",
        )


@router.get("/filedata/{qid}")
async def get_filedata(
    qid: str | UUID,
    qm: QuestionManagerDependency,
    storage: StorageDependency,
    storage_type: StorageTypeDep,
) -> List[FileData]:
    try:
        question = qm.get_question(qid)
        question_path = qm.get_question_path(question.id, storage_type)
        file_paths = storage.list_filepaths(question_path, recursive=True)
        logger.info("These are the file paths", file_paths)
        file_data = []
        for f in file_paths:
            if not f.is_file():
                continue
            try:
                mime_type, _ = mimetypes.guess_type(f.name)
                logger.info(f"File is {f} and mime type {mime_type}")
                if mime_type and (
                    mime_type.startswith("text")
                    or mime_type.startswith("application/json")
                ):
                    content = f.read_text(encoding="utf-8")
                else:
                    content = encode_image(f)
                    logger.info("Encoded image just fine")

                file_data.append(
                    FileData(
                        filename=f.name,
                        content=content,
                        mime_type=mime_type or "application/octet-stream",
                    )
                )
            except Exception as e:
                logger.warning(f"Could not read file {f}: {e}")
                file_data.append(
                    FileData(filename=f.name, content="Could not read file")
                )

        return file_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not get file data {e}")


@router.post("/files/{id}/{filename}/download")
async def download_question_file(
    qid: str | UUID,
    filename: str,
    qm: QuestionManagerDependency,
    storage: StorageDependency,
    fm: FileServiceDep,
    storage_type: StorageTypeDep,
):
    try:
        question = qm.get_question(qid)
        question_path = qm.get_question_path(question.id, storage_type)
        filepath = storage.get_file(question_path, filename)
        folder_name = f"{question.title}_download"

        zip_bytes = await fm.download_zip(files=[filepath], folder_name=folder_name)

        return Response(
            content=zip_bytes,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={folder_name}.zip"},
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not read file {filename}: {e}",
        )


@router.post("/files/{id}/download")
async def download_question(
    qid: str | UUID,
    qm: QuestionManagerDependency,
    storage: StorageDependency,
    fm: FileServiceDep,
    storage_type: StorageTypeDep,
):
    try:
        question = qm.get_question(qid)
        question_path = qm.get_question_path(question.id, storage_type)
        files = storage.list_filepaths(question_path)
        folder_name = f"{question.title}_download"

        logger.info("These are the files %s", files)

        zip_bytes = await fm.download_zip(files=files, folder_name=folder_name)

        return Response(
            content=zip_bytes,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={folder_name}.zip"},
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not get files {e}",
        )


@router.post("/{id}/upload_files")
async def upload_files_to_question(
    id: str | UUID,
    files: List[UploadFile],
    qm: QuestionManagerDependency,
    storage: StorageDependency,
    fm: FileServiceDep,
    storage_type: StorageTypeDep,
    auto_handle_images: bool = True,
):
    """
    Upload one or more files associated with a question.

    If `auto_handle_images` is True, image and document files (e.g., .png, .jpg, .pdf)
    are automatically saved into a `clientFiles` subdirectory within the question’s storage path.
    All other files are saved directly to the question’s root storage directory.

    Args:
        id (str | UUID): The unique identifier of the question.
        files (List[UploadFile]): List of files uploaded by the client.
        qm (QuestionManagerDependency): Handles question-related database queries.
        storage (StorageDependency): Manages local/cloud storage paths.
        fm (FileServiceDep): Handles saving files to disk or cloud.
        auto_handle_images (bool, optional): If True, stores image/document files separately.
            Defaults to True.

    Returns:
        dict: A response indicating successful file uploads.
    """
    try:
        # Retrieve the question record
        question = qm.get_question(id)
        if not question:
            logger.warning("Question with ID %s not found", id)
            raise HTTPException(status_code=404, detail=f"Question {id} not found")

        # Get the question’s main storage directory
        question_storage_path = storage.get_storage_path(
            str(qm.get_question_path(question.id, storage_type)), relative=False
        )
        logger.info("Resolved question storage path: %s", question_storage_path)

        # Separate image/document files from others
        image_and_doc_files = []
        other_files = []

        for uploaded_file in files:
            if not uploaded_file.filename:
                raise HTTPException(
                    status_code=status.HTTP_406_NOT_ACCEPTABLE,
                    detail="File must have a filename ",
                )
            ext = Path(uploaded_file.filename).suffix.lower()
            if ext in client_file_extensions:
                image_and_doc_files.append(uploaded_file)
            else:
                other_files.append(uploaded_file)

        # Define destination paths
        client_files_dir = Path(question_storage_path) / CLIENT_FILE_DIR

        # Upload files based on handling strategy
        if auto_handle_images:
            uploaded_client_files = await fm.save_files(
                image_and_doc_files, client_files_dir
            )
            uploaded_other_files = await fm.save_files(
                other_files, question_storage_path
            )
            return {
                "status": "ok",
                "detail": f"Uploaded {len(files)} files",
                "client_files": uploaded_client_files,
                "other_files": uploaded_other_files,
            }

        # If not handling separately, upload everything to root
        uploaded_files = await fm.save_files(files, question_storage_path)

        return {
            "status": "ok",
            "detail": f"Uploaded {len(files)} files",
            "files": uploaded_files,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error uploading files for question %s: %s", id, e)
        raise HTTPException(
            status_code=500,
            detail=f"Could not process file uploads: {e}",
        )
