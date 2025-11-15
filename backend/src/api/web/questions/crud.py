# --- Third-Party ---
from fastapi import APIRouter, HTTPException
from starlette import status

# --- Internal ---
from src.api.core import logger
from src.api.service.question.question_manager import QuestionManagerDependency
from src.api.service.storage_manager import StorageDependency
from src.api.models.models import Question
from src.api.models import *
from src.utils import safe_dir_name
from src.api.dependencies import StorageTypeDep

router = APIRouter(
    prefix="/questions",
    tags=[
        "questions",
    ],
)


@router.post("/")
async def create_question(
    qm: QuestionManagerDependency,
    storage: StorageDependency,
    question: QuestionData,
    storage_type: StorageTypeDep,
) -> Question:
    """
    Create a new question, store it in the database, and initialize its corresponding storage path.

    This function performs three main operations:
    1. Creates a new `Question` entry in the database via the `QuestionManagerDependency`.
    2. Generates a sanitized directory name for the question based on its title and ID.
    3. Initializes the appropriate storage path (local or cloud) and updates the database record
       with the correct relative path reference.

    Args:
        qm (QuestionManagerDependency): Manages database interactions for creating and committing the question.
        storage (StorageDependency): Handles file system or cloud storage initialization for the question.
        question (QuestionData): Input data model containing details of the question to be created.

    Returns:
        Question: The created `Question` SQLModel instance with updated storage path information.

    Raises:
        Exception: Propagates any error encountered during creation or storage initialization.
    """
    try:
        qcreated = await qm.create_question(question)
        # Handles the directoru creation for the question
        path_name = safe_dir_name(f"{qcreated.title}_{str(qcreated.id)[:8]}")
        # Creates the actual path
        path = storage.create_storage_path(path_name)
        # Storing the relative path in db
        relative_path = storage.get_storage_path(path, relative=True)
        qm.set_question_path(qcreated.id, relative_path, storage_type)
        # Commit the changes
        qm.session.commit()

        return qcreated
    except Exception:
        raise


@router.delete("/")
async def delete_all(
    qm: QuestionManagerDependency,
    storage: StorageDependency,
    delete_storage: bool = False,
):
    """
    Delete all questions from the database, with an optional flag to remove the entire storage directory.

    This endpoint removes every question record from the database. When the `delete_storage` flag is set to `True`,
    it additionally deletes the entire storage directory associated with question files.
    **Use caution**: enabling this flag will permanently remove *all* files and subdirectories under the storage path.

    Args:
        qm (QuestionManagerDependency): Handles bulk deletion of all question records from the database.
        storage (StorageDependency): Provides access to the file storage system (local or cloud).
        delete_storage (bool, optional): When `True`, deletes the entire storage directory on disk or in cloud storage.
            This operation is irreversible and should be used only when you are certain that all files can be removed.
            Defaults to `False`.

    Returns:
        dict: A confirmation message indicating successful deletion of all questions (and optionally the storage).

    Raises:
        Exception: Propagates any database or file system errors encountered during deletion.
    """
    try:
        qm.delete_all_questions()
        if delete_storage:
            logger.info("Deleting storage")
            storage.hard_delete()
        return {"status": "ok", "detail": "Deleted all questions"}
    except Exception as e:
        raise


@router.get("/{offset:int}/{limit:int}")
async def get_all_questions(
    qm: QuestionManagerDependency, offset: int = 0, limit: int = 100
) -> Sequence[Question]:
    """
    Retrieve a paginated list of all questions stored in the database.

    This endpoint queries the database for all available questions using pagination controls.
    It is primarily used for listing or browsing questions in bulk, supporting efficient
    batch retrieval through the `offset` and `limit` parameters.

    Args:
        qm (QuestionManagerDependency): Dependency responsible for database queries related to questions.
        offset (int, optional): The starting index for pagination. Defaults to 0.
        limit (int, optional): The maximum number of questions to retrieve. Defaults to 100.

    Returns:
        Sequence[Question]: A sequence of `Question` SQLModel instances representing the retrieved questions.

    Raises:
        Exception: Propagates any unexpected database or query-related errors during retrieval.
    """
    try:
        return qm.get_all_questions(offset, limit)
    except Exception:
        raise


@router.get("/{id}")
async def get_question(id: str | UUID, qm: QuestionManagerDependency) -> Question:
    """
    Retrieve a single question from the database by its ID.

    This endpoint queries the database for a specific `Question` instance.
    If no question is found matching the provided identifier, an HTTP 404 error is raised.

    Args:
        id (str | UUID): The unique identifier of the question to retrieve.
        qm (QuestionManagerDependency): Manages database operations for question retrieval.

    Returns:
        Question: The retrieved `Question` SQLModel instance.

    Raises:
        HTTPException: If the question does not exist in the database.
        Exception: Propagates any unexpected database or retrieval errors.
    """
    try:
        question = qm.get_question(id)
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Could not find question {id}",
            )
        return question
    except Exception:
        raise


@router.get("/{id}/all_data")
async def get_question_all_data(
    id: str | UUID, qm: QuestionManagerDependency, storage_type: StorageTypeDep
) -> QuestionMeta:
    """
    Retrieve a question and all associated metadata by its ID.

    This function fetches both the question record and its related metadata
    (such as relationships, tags, and supplemental data) for comprehensive inspection.

    Args:
        id (str | UUID): The unique identifier of the question to retrieve.
        qm (QuestionManagerDependency): Provides access to detailed question data and metadata.

    Returns:
        QuestionMeta: The combined question and metadata information.

    Raises:
        Exception: Propagates any database or data access errors encountered during retrieval.
    """
    try:
        question_data = await qm.get_question_data(id)
        question_data.question_path = qm.get_question_path(id, storage_type)
        return question_data
    except Exception:
        raise


@router.get("/{offset:int}/{limit:int}/all_data")
async def get_all_questions_data(
    qm: QuestionManagerDependency, offset: int, limit: int
) -> Sequence[QuestionMeta]:
    try:
        return await qm.get_all_question_data(offset, limit)
    except Exception:
        raise


@router.delete("/{id}")
async def delete_question(
    id: str | UUID,
    qm: QuestionManagerDependency,
    storage: StorageDependency,
    storage_type: StorageTypeDep,
):
    """
    Delete a question from the database and remove any associated stored files.

    This endpoint performs two operations:
    1. Retrieves the question by ID and ensures it exists.
    2. Deletes the database record and removes its storage location (local or cloud),
       depending on the active storage backend.

    If the question exists in the DB but does not have an associated storage path,
    the question is still deleted from the database, and a warning is logged to indicate
    that storage cleanup could not be performed.

    Args:
        id (str | UUID): The unique identifier of the question to delete.
        qm (QuestionManagerDependency): Handles database deletion of the question.
        storage (StorageDependency): Deletes storage resources, either locally or in cloud storage.

    Returns:
        dict: A confirmation response indicating successful deletion.

    Raises:
        HTTPException: If the question does not exist.
        Exception: Propagates any unexpected errors encountered during deletion.
    """
    try:
        question = await get_question(id, qm)
        if not question:
            raise HTTPException(
                status_code=404, detail="Question not found nothing to delete"
            )
        question_path = qm.get_question_path(
            question.id,
            storage_type,
        )

        assert qm.delete_question(id)
        if not question_path:
            logger.warning(
                "Question of ID: {question.id} Title: {question.title} does not have a storage path will still delete from database but may cause issues"
            )
            return {"status": "ok", "detail": "Deleted Question"}

        storage.delete_storage(question_path)
        return {"status": "ok", "detail": "Deleted Question"}

    except Exception:
        raise


@router.put("/{id}")
async def update_question(
    id: str | UUID,
    update: QuestionData,
    qm: QuestionManagerDependency,
    storage: StorageDependency,
    storage_type: StorageTypeDep,
    update_storage: bool = True,
) -> QuestionMeta:
    """
    Update a question in the database and optionally rename its associated storage directory.

    This endpoint updates a question’s database record and, if `update_storage` is enabled,
    renames the corresponding storage directory to reflect an updated title.
    The storage update ensures that both local and cloud storage paths remain consistent
    with the question’s current metadata.

    Args:
        id (str | UUID): Unique identifier of the question to update.
        update (QuestionData): Updated data for the question.
        qm (QuestionManagerDependency): Handles database operations related to questions.
        storage (StorageDependency): Manages storage paths and renaming operations.
        update_storage (bool): If True, renames the existing storage directory when the title changes.

    Returns:
        Question: The updated question model instance from the database.

    Raises:
        HTTPException: If the question cannot be found or an update operation fails.
        Exception: For any other unexpected errors during the update or rename process.
    """
    try:
        existing_question = qm.get_question(id)
        if not existing_question:
            logger.warning(f"Question with ID {id} not found — cannot update.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Question {id} not found.",
            )

        # Handle renaming the storage directory if required
        if update_storage and update.title:
            logger.info(
                f"Updating storage directory for question '{existing_question.title}' → '{update.title}'"
            )

            old_storage_path = qm.get_question_path(id, storage_type)
            if not old_storage_path:
                logger.error(f"No valid storage path found for question ID {id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Storage path missing for question {id}.",
                )

            # Generate a sanitized new directory name and resolve paths
            new_storage_name = safe_dir_name(f"{update.title}_{str(id)[:8]}")
            new_storage_path = storage.rename_storage(
                old_storage_path, new_storage_name
            )

            # Update the question's stored path reference
            updated_relative_path = storage.get_storage_path(
                new_storage_path, relative=True
            )
            qm.set_question_path(
                existing_question.id, updated_relative_path, storage_type
            )
            qm.session.commit()

            logger.info(
                f"Renamed storage path for question {id}: {old_storage_path} → {new_storage_path}"
            )

        # Proceed with updating database fields
        updated_question = await qm.update_question(id, update)
        logger.info(f"Successfully updated question {id}")

        return updated_question

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error while updating question {id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update question {e}")


@router.post("/filter")
async def filter_questions(
    filter_data: QuestionData, qm: QuestionManagerDependency
) -> Sequence[QuestionMeta]:
    try:
        logger.info("Retrieved filter %s", filter_data)
        return await qm.filter_questions(filter_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to filter question {e}")






# # TODO: Add test
# @router.post("/download_starter")
# async def download_starter(qm: QuestionManagerDependency):
#     try:
#         data = await qm.download_starter_templates()

#         # Create a new in-memory buffer
#         buffer = io.BytesIO()

#         # Open a ZipFile to write into that buffer
#         with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
#             for folder, bdata in data.items():
#                 # Ensure bdata is BytesIO or bytes
#                 if isinstance(bdata, io.BytesIO):
#                     content = bdata.getvalue()
#                 else:
#                     content = bdata

#                 # Write it into the zip archive
#                 zf.writestr(f"{folder}.zip", content)

#         # Reset pointer so StreamingResponse can read from start
#         buffer.seek(0)

#         return StreamingResponse(
#             buffer,
#             media_type="application/zip",
#             headers={
#                 "Content-Disposition": 'attachment; filename="starter_templates.zip"'
#             },
#         )
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Could not download starter: {e}",
#         )
