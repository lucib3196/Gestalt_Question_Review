# Stdlib
import asyncio
from pathlib import Path
from typing import List, Literal, Sequence
from uuid import UUID

# Internal
from src.api.core import logger
from src.api.database import SessionDep
from src.api.models.models import Question
from src.api.response_models import FileData
from src.api.service.crud import question_crud as qc
from src.api.service.storage import StorageService
from src.utils import safe_dir_name
from sqlmodel import select
from fastapi import HTTPException
from starlette import status
import io
from typing import Dict, Any
from pydantic import ValidationError
from src.api.database import question as qdb
from src.api.service.file_handler import FileService


from src.api.core.config import get_settings

settings = get_settings()


class QuestionManager:
    """Manage creation, retrieval, and file operations for questions."""

    def __init__(
        self, storage_service: StorageService, storage_type: Literal["local", "cloud"]
    ):
        """Initialize with a storage backend and storage type."""
        self.storage = storage_service
        self.storage_type: Literal["local", "cloud"] = storage_type
        self.base_path = self.storage.get_base_path()
        self.base_name = self.storage.get_base_name()

        # TODO: Need to make this a bit better
        ## General file service mostly just used for the starter template download
        self.file_service = FileService(settings.ROOT_PATH)

    # ---------------------------
    # Question Lifecycle
    # ---------------------------
    async def create_question(
        self, question: Question | dict, session: SessionDep, exists: bool = False
    ) -> Question:
        """Create a new question in DB and storage."""
        try:
            q = await qc.create_question(question, session)
            logger.info("Created question successfully %s", q.title)
        except Exception as e:
            logger.error("Failed to create question in DB: %s", e)
            raise

        try:
            logger.info("Setting up Question")
            qname = safe_dir_name((q.title or "").strip())

            if not qname:
                logger.error("Question title is None")
                raise ValueError("Question title cannot be None")

            # Always append the ID to guarantee uniqueness
            qname = f"{qname}_{q.id}"

            # Create directory if it doesn’t exist already
            if not exists and not self.storage.does_storage_path_exist(qname):
                self.storage.create_storage_path(qname)

            # Point DB record to the correct directory
            q = self.set_question_path(q, qname)

            # Refresh DB object
            q = await qc.safe_refresh_question(q, session)
            return q

        except Exception as e:
            logger.error(
                "Failed to set up storage for question %s: %s",
                getattr(q, "title", None),
                e,
            )
            raise

    async def update_question(
        self, question_id: str | UUID, session: SessionDep, **kwargs
    ):
        """Update question metadata in the DB."""
        try:
            return await qc.edit_question_meta(question_id, session, **kwargs)
        except Exception as e:
            logger.error(f"Failed to update question {str(e)}")
            raise

    async def get_question(self, question_id: str | UUID, session: SessionDep):
        """Retrieve a question by ID."""
        try:
            return await qc.get_question_by_id(question_id, session)
        except Exception as e:
            logger.error("Failed to retrieve question %s: %s", question_id, e)
            raise

    # Retrieving all Questions
    # TODO: Add a test for this
    async def get_question_data(
        self, question_id: UUID | str, session: SessionDep
    ) -> Question:
        try:
            retrieved_question = await qdb.get_question_data(question_id, session)
            return Question.model_validate(retrieved_question)
        except ValidationError as e:
            # Log the validation issue for debugging
            logger.error("Validation failed for Question %s: %s", question_id, e)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid question data: {e.errors()}",
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Question not Found"
            )
        except Exception as e:
            logger.error("Failed to retrieve question data %s: %s", question_id, e)
            raise

    async def get_question_identifier(
        self, question_id: str | UUID, session: SessionDep
    ):
        """Get the storage identifier (folder/blob name) for a question."""
        q = await self.get_question(question_id, session)
        if q is None:
            logger.error("Failed to get a question")
            raise ValueError("Question is None")

        try:
            qpath = self.get_question_path(q)
            return Path(qpath).name if qpath else None
        except Exception as e:
            logger.error(
                "Error while extracting identifier for question %s: %s", question_id, e
            )
            raise

    # Retrieving all Questions
    # TODO: Add a test for this
    async def get_all_questions(
        self, offset: int, limit: int, session: SessionDep
    ) -> Sequence[Question] | None:
        try:
            if self.storage_type == "cloud":
                filter = Question.blob_path != None
            else:
                filter = Question.local_path != None

            results = session.exec(
                select(Question).where(filter).offset(offset).limit(limit)
            ).all()
            return results
        except Exception as e:
            logger.error("Error while getting questions %s: %s", e)
            raise

    # TODO: Add a test for this service
    async def get_all_questions_full(
        self, offset: int, limit: int, session: SessionDep
    ):
        try:
            all_questions = await self.get_all_questions(offset, limit, session)
            results = await asyncio.gather(
                *[self.get_question_data(q.id, session) for q in all_questions or []]
            )
            return results
        except Exception as e:
            raise

    # TODO Add a test for this service
    async def filter_questions(self, session: SessionDep, **kwargs):
        try:
            if self.storage_type == "cloud":
                filter = Question.blob_path != None
            else:
                filter = Question.local_path != None

            return await qc.filter_questions_meta(
                session,
                [filter],
                **kwargs,
            )
        except Exception as e:
            raise

    # ---------------------------
    # File Operations
    # ---------------------------
    async def save_file_to_question(
        self,
        question_id: str | UUID,
        session: SessionDep,
        file: FileData,
        overwrite: bool = False,
    ) -> bool:
        """Save a single file to a question directory."""
        try:
            await self.get_question(question_id, session)
            identifier = await self.get_question_identifier(question_id, session)
            if not identifier:
                raise ValueError("Could not resolve question identifier")

            self.storage.save_file(identifier, file.filename, file.content, overwrite)
            logger.info(f"Wrote file {file.filename} for question {question_id}")
            return True
        except Exception as e:
            logger.error(
                "Failed saving file %s for question %s: %s",
                file.filename,
                question_id,
                e,
            )
            raise

    async def save_files_to_question(
        self,
        question_id: str | UUID,
        session: SessionDep,
        files: List[FileData],
        overwrite: bool = False,
    ) -> bool:
        """Save multiple files to a question directory."""
        try:
            await asyncio.gather(
                *[
                    self.save_file_to_question(question_id, session, f, overwrite)
                    for f in files
                ]
            )
            return True
        except Exception as e:
            logger.error("Failed to save files to question %s: %s", question_id, e)
            raise

    async def read_file(
        self, question_id: str | UUID, session: SessionDep, filename: str
    ) -> bytes | None:
        """Retrieve a file from a question directory."""
        try:
            qidentifier = await self.get_question_identifier(question_id, session)
            if not qidentifier:
                raise ValueError("Could not resolve question identifier")
            return self.storage.get_file(qidentifier, filename)
        except Exception as e:
            logger.error("Failed to get file %s for question %s", filename, question_id)
            raise

    async def get_all_files(
        self, question_id: str | UUID, session: SessionDep
    ) -> List[str]:
        """Retrieve all file names for a given question."""
        try:
            qidentifier = await self.get_question_identifier(question_id, session)
            if not qidentifier:
                raise ValueError("Could not resolve question identifier")
            return self.storage.list_file_names(qidentifier)
        except Exception as e:
            logger.error("Failed to get files for question %s", question_id)
            raise

    async def read_all_files(
        self, question_id: str | UUID, session: SessionDep
    ) -> List[FileData]:
        try:
            files = await self.get_all_files(question_id, session)

            # Await to actually run and collect results
            contents = await asyncio.gather(
                *[self.read_file(question_id, session, f) for f in files]
            )

            # Pair each filename with its content
            file_data = [
                FileData(filename=f, content=c) for f, c in zip(files, contents)
            ]
            return file_data

        except Exception as e:
            logger.error(
                "Failed to read all files for question %s Error: %s",
                question_id,
                str(e),
            )
            raise

    # ---------------------------
    # Deletion
    # ---------------------------
    async def delete_question(self, question_id: str | UUID, session: SessionDep):
        """Delete a question and all its files."""
        try:
            qidentifier = await self.get_question_identifier(question_id, session)
            if not qidentifier:
                raise ValueError("Could not resolve question identifier")
            await qc.delete_question_by_id(question_id, session)
            self.storage.delete_storage(qidentifier)
            return True
        except Exception as e:
            logger.error("Failed to delete question %s: %s", question_id, e)
            raise

    async def delete_question_file(
        self, question_id: str | UUID, session: SessionDep, filename: str
    ):
        """Delete a single file from a question."""
        try:
            qidentifier = await self.get_question_identifier(question_id, session)
            if not qidentifier:
                raise ValueError("Could not resolve question identifier")
            self.storage.delete_file(qidentifier, filename)
        except Exception as e:
            logger.error("Failed to delete file %s %s: %s", question_id, filename, e)
            raise

    # TODO: Test
    async def delete_all_questions(self, session: SessionDep):
        try:
            all_questions = await self.get_all_questions(
                offset=0, limit=100, session=session
            )
            logger.debug(f"These are all the questions, %s", all_questions)
            if not all_questions:
                logger.info("No questions found to delete.")
                return {"deleted_count": 0, "detail": "No questions to delete"}

            logger.debug("Deleting %d questions: %s", len(all_questions), all_questions)
            question_ids = [
                q["id"] if isinstance(q, dict) else q.id for q in all_questions
            ]
            results = await asyncio.gather(
                *[
                    self.delete_question(UUID(str(qid)), session)
                    for qid in question_ids
                ],
                return_exceptions=True,
            )
            deleted_count = sum(1 for r in results if r is True)
            errors = [str(r) for r in results if isinstance(r, Exception)]

            if errors:
                logger.error("Errors occurred while deleting questions: %s", errors)
                return {
                    "deleted_count": deleted_count,
                    "errors": errors,
                    "detail": "Some deletions failed",
                }

            return {
                "deleted_count": deleted_count,
                "detail": "All questions deleted successfully",
            }
        except Exception as e:
            raise e

    # Download
    # TODO: Test
    async def download_question(
        self, session: SessionDep, question_id: UUID | str
    ) -> bytes | io.BytesIO:
        qidentifier = await self.get_question_identifier(question_id, session)
        if not qidentifier:
            raise ValueError("Could not resolve question identifier")
        return await self.storage.download_question(qidentifier)

    # TODO Fix this and add a test for this
    async def download_starter_templates(self) -> Dict[str, bytes]:
        try:
            adaptive_template = (
                Path(settings.ROOT_PATH) / "starter_templates" / "AdaptiveStarter"
            )
            nonadaptive_template = (
                Path(settings.ROOT_PATH) / "starter_templates" / "NonAdaptive"
            )
            adaptive_bytes = await self.file_service.download_zip(
                [p for p in adaptive_template.iterdir()],
                folder_name="Adaptive Template",
            )
            nonadaptive_bytes = await self.file_service.download_zip(
                [p for p in nonadaptive_template.iterdir()],
                folder_name="NonAdaptiveStarter",
            )
            return {
                "adaptiveTemplate": adaptive_bytes,
                "NonAdaptiveTemplate": nonadaptive_bytes,
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not download starter template {str(e)}",
            )

    # ---------------------------
    # Helpers
    # ---------------------------
    # TODO: Test
    def get_question_path(self, q: Question):
        """Return the stored path (local or cloud) for a question."""
        try:
            if self.storage_type == "local":
                return q.local_path
            elif self.storage_type == "cloud":
                return q.blob_path
        except Exception as e:
            logger.error(
                "Failed to get question path for %s: %s", getattr(q, "title", None), e
            )
            raise

    # TODO: Test
    def set_question_path(self, q: Question, qname: str) -> Question:
        """Assign storage path (local or cloud) to a question object."""
        logger.info("Setting question path for %s", q.title)

        relative_path = self.storage.get_relative_storage_path(qname)

        if isinstance(relative_path, Path):
            relative_path = relative_path.as_posix()

        try:
            # Assign based on storage type
            if self.storage_type == "local":
                q.local_path = relative_path
                logger.info("Local question path set → %s", q.local_path)

            elif self.storage_type == "cloud":
                q.blob_name = relative_path
                logger.info("Cloud question path set → %s", q.blob_path)

            else:
                raise ValueError(f"Unknown storage type: {self.storage_type}")

            return q

        except Exception as e:
            title = getattr(q, "title", "<unknown>")
            msg = f"Failed to set question path for '{title}': {str(e)}"
            logger.error(msg)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=msg,
            ) from e

    # TODO: Test
    def get_basename(self) -> str | Path:
        """Return the base directory/bucket name from storage."""
        try:
            return self.storage.get_base_path()
        except Exception as e:
            logger.error("Failed to get basename from storage: %s", e)
            raise
