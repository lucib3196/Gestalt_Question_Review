from functools import lru_cache
from typing import Annotated, List, Optional
from fastapi import Depends
from src.api.core import logger
from src.api.dependencies import StorageType, StorageTypeDep
from src.api.models import FileData, QuestionData
from src.api.models.models import Question
from src.api.service.question.question_manager import (
    QuestionManager,
    QuestionManagerDependency,
)
from src.api.service.storage_manager import StorageDependency, StorageService
from src.utils import safe_dir_name


class QuestionResourceService:
    """Service that coordinates storage and database operations for questions."""

    def __init__(
        self,
        qm: QuestionManager,
        storage_manager: StorageService,
        storage_type: StorageType,
    ):
        self.qm = qm
        self.storage_manager = storage_manager
        self.storage_type = storage_type

    async def create_question(
        self,
        question_data: QuestionData,
        files: Optional[List[FileData]] = None,
    ) -> Question:
        """Create a question and optionally save associated files."""
        logger.info(
            f"[QuestionResourceService] Starting creation for '{question_data.title}'"
        )

        # Step 1: Create question record
        qcreated = await self.qm.create_question(question_data)
        logger.debug(f"[QuestionResourceService] DB entry created (ID={qcreated.id})")

        # Step 2: Prepare storage directories
        path_name = safe_dir_name(f"{qcreated.title}_{str(qcreated.id)[:8]}")
        path = self.storage_manager.create_storage_path(path_name)
        relative_path = self.storage_manager.get_storage_path(path, relative=True)
        abs_path = self.storage_manager.get_storage_path(path, relative=False)
        logger.debug(f"[QuestionResourceService] Storage paths ready: {abs_path}")

        # Step 3: Update DB with storage reference
        self.qm.set_question_path(qcreated.id, relative_path, self.storage_type)  # type: ignore
        self.qm.session.commit()
        logger.info(
            f"[QuestionResourceService] Question path updated and committed (ID={qcreated.id})"
        )

        # Step 4: Save uploaded files (if any)
        for f in files or []:
            self.storage_manager.save_file(
                abs_path, filename=f.filename, content=f.content
            )
            logger.debug(f"[QuestionResourceService] Saved file '{f.filename}'")

        logger.info(
            f"[QuestionResourceService] Question '{qcreated.title}' saved successfully"
        )
        return qcreated


@lru_cache
def get_question_resource(
    qm: QuestionManagerDependency,
    storage: StorageDependency,
    storage_type: StorageTypeDep,
):
    return QuestionResourceService(qm, storage, storage_type)


QuestionResourceDepencency = Annotated[
    QuestionResourceService, Depends(get_question_resource)
]
