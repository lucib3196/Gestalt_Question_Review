# --- Standard Library ---
import asyncio
from typing import List, Optional, Sequence, Union
from uuid import UUID

# --- Third-Party ---
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import ValidationError
from starlette import status
import io
from fastapi.responses import StreamingResponse

# --- Internal ---
from src.api.core import logger
from src.api.database import SessionDep
from src.api.dependencies import QuestionManagerDependency
from src.api.models import Question
from src.api.models.question_model import QuestionMeta
from src.api.response_models import *
from src.api.service.file_handler import FileService
from src.utils import normalize_kwargs, serialized_to_dict
from src.api.response_models import SuccessDataResponse
import json
from typing import Literal
from src.api.models import Question
from pydantic import ValidationError

router = APIRouter(prefix="/questions", tags=["Questions", "local", "dev"])

excluded_path_names = ["downloads"]
metadata_name = "metadata.json"

SyncStatus = Literal[
    "missing_metadata",  # metadata.json not found
    "invalid_metadata_json",  # JSON decode error
    "missing_id",  # ID field not found in metadata
    "not_in_database",  # Metadata ID not found in DB
]


class UnsyncedQuestion(BaseModel):
    question_name: str
    question_path: str
    detail: str
    status: SyncStatus
    metadata: str | None


class SyncMetrics(BaseModel):
    total_found: int
    synced: int
    skipped: int
    failed: int


class SyncResponse(BaseModel):
    metrics: SyncMetrics
    synced_questions: List["Question"]
    skipped_questions: List["UnsyncedQuestion"]
    failed_questions: List[str]  # store file name or reason


async def check_question_sync_status(
    question: Path,
    session: SessionDep,
    qm: QuestionManagerDependency,
    metadata_name: str = "metadata.json",
) -> Union["Question", "UnsyncedQuestion"]:
    """
    Verify if a given question folder is properly synchronized with the database.

    The function performs the following checks:
    1. Ensures `metadata.json` exists.
    2. Verifies that the file contains a valid question ID.
    3. Confirms that the ID corresponds to an entry in the database.

    Returns:
        - `Question`: if the question is properly synced with the DB.
        - `UnsyncedQuestion`: with detailed reasoning if not synced.
    """

    metadata_path = question / metadata_name
    logger.info(
        f"🔍 Checking sync status for question directory: {question.as_posix()}"
    )
    relative_path = Path(question).as_posix()
    # --- Step 1: Ensure metadata.json exists ---
    if not metadata_path.exists():
        detail = (
            f"No `{metadata_name}` found in {question.name}. "
            "This question cannot be indexed or referenced until metadata is generated."
        )

        logger.warning(detail)
        return UnsyncedQuestion(
            question_name=question.name,
            question_path=relative_path,
            detail=detail,
            status="missing_metadata",
            metadata=None,
        )

    logger.info(f"✅ Found metadata file for {question.name}")

    # --- Step 2: Parse metadata.json ---
    try:
        question_data = json.loads(metadata_path.read_text())
    except json.JSONDecodeError as e:
        detail = f"Invalid JSON in {metadata_name}: {e}"
        logger.error(detail)
        return UnsyncedQuestion(
            question_name=question.name,
            question_path=relative_path,
            detail=detail,
            status="invalid_metadata_json",
            metadata=None,
        )

    question_id = question_data.get("id")
    if not question_id:
        detail = (
            f"`{metadata_name}` found for {question.name}, but no 'id' key present. "
            "This likely means the question was never inserted into the database."
        )
        logger.warning(detail)
        return UnsyncedQuestion(
            question_name=question.name,
            question_path=relative_path,
            detail=detail,
            status="missing_id",
            metadata=json.dumps(question_data),
        )

    logger.info(f"🗂 Found Question ID: {question_id}")

    # --- Step 3: Confirm question exists in DB ---
    qdb = await qm.get_question(question_id, session)
    if qdb is None:
        detail = (
            f"Metadata contains Question ID {question_id}, but no corresponding record was found in the database. "
            "Run the synchronization process to register this question."
        )
        logger.warning(detail)
        return UnsyncedQuestion(
            question_name=question.name,
            question_path=relative_path,
            detail=detail,
            status="not_in_database",
            metadata=json.dumps(question_data),
        )

    logger.info(
        f"✅ Question {question.name} is properly synced with the database (ID: {question_id})"
    )
    return qdb


async def get_all_unsynced(
    path: Path, session: SessionDep, qm: QuestionManagerDependency
):
    tasks = [
        check_question_sync_status(question, session, qm)
        for question in path.iterdir()
        if question.name not in excluded_path_names
    ]
    results = await asyncio.gather(*tasks)

    return [r for r in results if isinstance(r, UnsyncedQuestion)]


@router.post("/check_unsync", response_model=List[UnsyncedQuestion])
async def view_local(session: SessionDep, qm: QuestionManagerDependency):
    path = Path(qm.base_path).resolve()
    if not path.exists():
        logger.debug("Creating base path. It does not exist")
        path.mkdir(parents=True, exist_ok=True)

    return await get_all_unsynced(path, session, qm)


@router.post("/sync_questions", response_model=SyncResponse)
async def sync_questions(session: SessionDep, qm: QuestionManagerDependency):
    """
    Synchronize all unsynced questions in the base directory with the database.

    Steps:
    1. Ensure base path exists.
    2. Detect unsynced questions (missing, invalid, or outdated metadata).
    3. Attempt to validate and insert questions into DB.
    4. Return a structured summary with metrics.
    """

    base_path = Path(qm.base_path).resolve()
    if not base_path.exists():
        logger.warning(f"⚠️ Base directory {base_path} not found — creating it.")
        base_path.mkdir(parents=True, exist_ok=True)

    unsynced_questions: List[UnsyncedQuestion] = await get_all_unsynced(
        base_path, session, qm
    )

    synced_questions: List[Question] = []
    skipped_questions: List[UnsyncedQuestion] = []
    failed_questions: List[str] = []

    logger.info(f"🔍 Found {len(unsynced_questions)} unsynced questions to process.")

    for uq in unsynced_questions:
        # --- Skip if no metadata file ---
        if not getattr(uq, "metadata", None):
            logger.warning(f"⏩ Skipping {uq.question_name}: no metadata available.")
            skipped_questions.append(uq)
            continue

        # --- Try to validate metadata ---
        try:
            metadata_dict = json.loads(str(uq.metadata))
            qvalidated = Question.model_validate(
                metadata_dict, context={"extra": "ignore"}
            )
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON for {uq.question_name}: {e}")
            failed_questions.append(f"{uq.question_name} (invalid JSON)")
            continue
        except ValidationError as e:
            logger.error(f"Validation failed for {uq.question_name}: {e}")
            failed_questions.append(f"{uq.question_name} (schema mismatch)")
            continue

        # --- Try to insert into DB ---
        try:
            # Prevent creation of a new folder — reuse the existing one by renaming it
            created_q = await qm.create_question(qvalidated, session, exists=True)
            synced_questions.append(created_q)

            old_path = Path(uq.question_path).resolve()
            folder_name = Path(str(created_q.local_path)).name

            new_path = (Path(qm.base_path) / folder_name).resolve()

            logger.debug(
                f"This is the old path {old_path} \n here is the new path {new_path}"
            )

            # Rename the unsynced folder to its proper synced location
            if old_path.exists():
                logger.info(f"Renaming {old_path} → {new_path}")
                old_path.rename(new_path)
            else:
                logger.warning(f"Old path not found: {old_path}")

            logger.info(f"✅ Synced question: {uq.question_name}")

        except Exception as e:
            logger.exception(f"Failed to create question {uq.question_name}: {e}")
            failed_questions.append(f"{uq.question_name} (DB error)")

    # --- Metrics summary ---
    metrics = SyncMetrics(
        total_found=len(unsynced_questions),
        synced=len(synced_questions),
        skipped=len(skipped_questions),
        failed=len(failed_questions),
    )

    logger.info(
        f"📊 Sync Summary — Found: {metrics.total_found}, "
        f"Synced: {metrics.synced}, Skipped: {metrics.skipped}, Failed: {metrics.failed}"
    )

    return SyncResponse(
        metrics=metrics,
        synced_questions=synced_questions,
        skipped_questions=skipped_questions,
        failed_questions=failed_questions,
    )
