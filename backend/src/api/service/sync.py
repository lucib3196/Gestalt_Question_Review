# --- Standard Library ---
import asyncio
import json
from collections import defaultdict
from typing import List, Literal, Sequence, Union

# --- Third-Party ---
from pydantic import ValidationError

# --- Internal ---
from src.api.core import logger
from src.api.models import *
from src.api.models.models import Question
from src.api.models.sync_models import *
from src.api.service.question.question_manager import QuestionManagerDependency
from src.api.service.storage_manager import StorageDependency
from src.utils import safe_dir_name, to_serializable


metadata_name = ["metadata.json", "info.json"]
excluded_path_names = ["downloads"]


async def resolve_metadata_path(
    question: Path, metadata_name: List[str] = metadata_name
) -> Path | None:
    for m in metadata_name:
        metadata_path = question / m
        if metadata_path.exists():
            logger.info(f"Found metadata path for filename {m}")
            return metadata_path
    return None


async def check_question_sync_status(
    question: Path,
    qm: QuestionManagerDependency,
    metadata_name: List[str] = metadata_name,
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
    relative_path = Path(question).as_posix()
    logger.info("Checking the relative path for the sync %s", relative_path)
    metadata = await resolve_metadata_path(question)
    if metadata is None:
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

    try:
        question_data = json.loads(metadata.read_text())
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
    try:
        qdb = qm.get_question(question_id)
    except Exception:
        logger.info("Question is not in database")
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
    path: Path, qm: QuestionManagerDependency
) -> Sequence[UnsyncedQuestion]:
    try:
        tasks = [
            check_question_sync_status(question, qm)
            for question in path.iterdir()
            if question.name not in excluded_path_names
        ]
        results = await asyncio.gather(*tasks)
        return [r for r in results if isinstance(r, UnsyncedQuestion)]
    except Exception as e:
        raise ValueError(f"Could not check the unsynced questions {e}")


async def check_local_unsync(
    storage: StorageDependency, qm: QuestionManagerDependency
) -> Sequence[UnsyncedQuestion]:
    try:

        path = Path(storage.get_base_path()).resolve()
        logger.info(f"Checking the path {path}")
        if not path.exists():
            logger.debug("Creating base path. It does not exist")
            path.mkdir(parents=True, exist_ok=True)
        return await get_all_unsynced(path, qm)
    except Exception as e:
        logger.info(f"Could not check unsync {e}")
        raise e


async def sync_question(
    unsynced: UnsyncedQuestion,
    qm: QuestionManagerDependency,
    storage: StorageDependency,
) -> SyncStatus:
    # Check metadata
    if not getattr(unsynced, "metadata", None):
        logger.warning(f"⏩ Skipping {unsynced.question_name}: no metadata available.")
        return "missing_metadata"

    # Validate the metadata
    try:
        metadata_dict = json.loads(str(unsynced.metadata))
        qvalidated = QuestionData.model_validate(metadata_dict, context={"extra": "ignore"})
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON for {unsynced.question_name}: {e}")
        return "invalid_metadata_json"
    except ValidationError as e:
        logger.error(f"Validation failed for {unsynced.question_name}: {e}")
        return "invalid question schema"

    # Write and save the question
    try:
        qcreated = await qm.create_question(qvalidated.model_dump())
        # Handle path
        old_path = Path(unsynced.question_path).resolve()
        new_path = safe_dir_name(f"{qcreated.title}_{str(qcreated.id)[:8]}")
        new_path = Path(storage.get_base_path()) / new_path
        logger.info("This is the db_path")

        if old_path.exists():
            logger.info(f"Renaming {old_path} → {new_path}")
            new_path = storage.rename_storage(old_path, new_path)
        else:
            new_path = storage.create_storage_path(new_path)

        db_path = storage.get_storage_path(new_path, relative=True)
        logger.info("This is the db_path %s ", db_path)

        qm.set_question_path(qcreated.id, db_path, storage_type="local")

        # Write the question data to the folder
        question_data = await qm.get_question_data(qcreated.id)
        meta_path = (Path(new_path) / "info2.json").resolve()
        meta_path.write_text(
            json.dumps(
                to_serializable(question_data.model_dump()),
                indent=2,
                ensure_ascii=False,
            )
        )
        logger.info(f"✅ Synced question: {unsynced.question_name}")
        return "success"
    except Exception as e:
        logger.exception(f"Failed to create question {unsynced.question_name}: {e}")
        return "failed to create question"


async def sync_questions(
    qm: QuestionManagerDependency, storage: StorageDependency
) -> SyncMetrics:
    path = Path(storage.get_base_path()).resolve()
    logger.info("Checking the path %s", path)
    if not path.exists():
        logger.warning(f"⚠️ Base directory {path} not found — creating it.")
        path.mkdir(parents=True, exist_ok=True)
    unsynced_questions: Sequence[UnsyncedQuestion] = await get_all_unsynced(path, qm)

    logger.info(f"🔍 Found {len(unsynced_questions)} unsynced questions to process.")
    sync_results = await asyncio.gather(
        *[sync_question(q, qm, storage) for q in unsynced_questions]
    )

    categorized = defaultdict(list)
    for question, status in zip(unsynced_questions, sync_results):
        categorized[status].append(question.question_name)

    success_count = len(categorized.get("success", []))
    failed_count = sum(len(v) for k, v in categorized.items() if k != "success")
    metrics = SyncMetrics(
        total_found=len(unsynced_questions),
        synced=success_count,
        failed=failed_count,
    )
    return metrics


async def prune_question(
    q: Question, qm: QuestionManagerDependency, storage: StorageDependency
) -> Literal["ok", "deleted", "bug"]:
    if not q.local_path:
        qm.delete_question(q.id)
        return "deleted"
    question_path = Path(storage.get_storage_path(q.local_path, relative=False))
    if question_path.exists():
        logger.debug(f"✅ Folder exists for '{q.title}' → {question_path}")
        return "ok"
    else:
        try:
            qm.delete_question(q.id)
            return "deleted"
        except Exception as e:
            logger.exception(f"⚠️ Failed to delete '{q.title}' from DB: {e}")
            return "bug"


async def prune_questions(
    qm: QuestionManagerDependency, storage: StorageDependency
) -> FolderCheckMetrics:
    all_questions = qm.get_all_questions(
        0,
        1000,
    )
    if not all_questions:
        logger.info("📂 No questions found in the database.")
        return FolderCheckMetrics(
            total_checked=0,
            deleted_from_db=0,
            still_valid=0,
        )

    total_checked = len(all_questions)
    prune_status = await asyncio.gather(
        *[prune_question(q, qm, storage) for q in all_questions]
    )

    categorized = defaultdict(list)
    for question, status in zip(all_questions, prune_status):
        categorized[status].append(question.title)

    deleted_count = len(categorized.get("delete", []))
    still_valid = len(categorized.get("ok", []))
    bug = len(categorized.get("bug", []))

    metrics = FolderCheckMetrics(
        total_checked=total_checked,
        deleted_from_db=deleted_count,
        still_valid=still_valid,
        bug=bug,
    )
    return metrics
