import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
from src.api.core import logger
from src.api.dependencies import (
    QuestionManagerDependency,
    get_question_manager,
    QuestionManager,
)
from src.api.models.models import QuestionMeta
from pydantic import BaseModel, PositiveInt, ValidationError
import json
from src.api.database import get_session, Session
import asyncio
from fastapi import HTTPException
from typing import cast
from src.api.core import settings

from src.api.response_models import FileData
import json
from pathlib import Path
from fastapi import HTTPException
from pydantic import ValidationError
from src.utils import to_serializable


class LocalQuestionWatcher:
    """
    Watches for local question uploads/changes and processes metadata.json
    to create or update questions in the database.
    """

    def __init__(
        self,
        question_manager: QuestionManager,
        session: Session,
        base_dir: str | Path = settings.BASE_PATH,
    ):
        """
        Args:
            question_manager: Handles creation/retrieval of questions.
            session: Database session for persistence.
            base_dir: Base directory where question folders are stored.
        """
        self.qm = question_manager
        self.session = session
        self.base_dir = Path(base_dir)

    async def process_new_upload(self, directory_path: str | Path):
        """
        Handle a new question directory upload.

        Args:
            directory_path: Path to the uploaded directory.
        """
        directory = Path(directory_path)
        logger.info("📂 Detected new upload: %s", directory.name)
        await self._process_metadata_file(directory)

    async def _process_metadata_file(self, question_dir: Path):
        """
        Look for and process metadata.json in the question directory.

        Args:
            question_dir: Path to the question directory.
        """
        metadata_file = question_dir / "metadata.json"

        if not metadata_file.exists():
            logger.warning("⚠️ No metadata.json found in %s; skipping.", question_dir)
            return

        try:
            raw_content = metadata_file.read_text(encoding="utf-8")
            logger.debug(
                "Raw metadata.json content from %s: %s", question_dir, raw_content
            )

            metadata_dict = json.loads(raw_content)
            question_meta = QuestionMeta(**metadata_dict)
            logger.info("✅ Parsed metadata for question: %s", question_meta.title)

            if question_meta.id:
                await self._sync_with_database(question_meta, question_dir)

        except HTTPException:
            raise  # Let FastAPI bubble this up
        except ValidationError as e:
            logger.error("❌ Metadata validation failed for %s: %s", question_dir, e)
        except json.JSONDecodeError as e:
            logger.error("❌ Invalid JSON in %s: %s", metadata_file, e)

    async def _sync_with_database(
        self, question_meta: QuestionMeta, question_dir: Path
    ):
        """
        Ensure the question exists in the database; if not, create it.
        If created, rename the directory to match the assigned path.

        Args:
            question_meta: Parsed metadata for the question.
            question_dir: Path to the question directory.
        """
        logger.info("🔎 Checking database for question ID %s", question_meta.id)
        if question_meta.id is None:
            raise NotImplementedError(
                "Case for questions without ID is not implemented yet."
            )

        existing_question = await self.qm.get_question(question_meta.id, self.session)

        if existing_question:
            logger.info("ℹ️ Question %s already exists in database.", question_meta.id)
            return

        # Create a new question without the provided ID (invalid in DB)
        logger.info(
            "➕ Creating new question from metadata (no valid DB record found)."
        )
        question_data = question_meta.model_dump(exclude={"id"})
        created_question = await self.qm.create_question(
            question_data, self.session, exists=True
        )
        logger.info("✅ Created new question with DB ID %s", created_question.id)

        # Refresh with full DB data
        db_question_data = await self.qm.get_question_data(
            created_question.id, session=self.session
        )
        logger.debug("🔄 Full question data retrieved: %s", db_question_data)

        # Rename the directory to match DB’s expected path
        new_directory_path = self.base_dir / str(db_question_data.local_path)
        logger.info(
            "📂 Renaming directory from %s → %s", question_dir, new_directory_path
        )
        question_dir.rename(new_directory_path)

        new_meta = FileData(
            filename="metadata.json",
            content=to_serializable(db_question_data.model_dump()),
        )
        await self.qm.save_file_to_question(
            db_question_data.id, self.session, new_meta, overwrite=True
        )
        logger.info("Updated metadata file of question")


class MyHandler(FileSystemEventHandler):

    def __init__(self, local_wd: LocalQuestionWatcher, loop: asyncio.AbstractEventLoop):
        self.local_wd = local_wd
        self.loop = loop

    def on_created(self, event):
        if event.is_directory:
            logger.info("Created a new directory %s", event.src_path)

            # Create the event loop for running the asynchronous code
            self.loop.create_task(
                self.local_wd.process_new_upload(cast(str, event.src_path))
            )
        if not event.is_directory:
            logger.info(f"File created: {event.src_path}")

    def on_modified(self, event):
        if not event.is_directory:
            logger.info(f"File modified: {event.src_path}")

    def on_deleted(self, event):
        if not event.is_directory:
            logger.info(f"File deleted: {event.src_path}")

    def on_moved(self, event):
        if not event.is_directory:
            logger.info(f"File moved: {event.src_path} → {event.dest_path}")


async def run_watchdog(path_to_watch: str | Path):
    qm = get_question_manager()
    gen = get_session()
    session = next(gen)  # open session
    if qm.storage_type != "local":
        logger.info("Watchdogs Disabled for non local storage types")
        return
    logger.info("Initializing Local WatchDogs")
    local = LocalQuestionWatcher(qm, session)

    loop = asyncio.get_running_loop()
    handler = MyHandler(local_wd=local, loop=loop)
    observer = Observer()
    observer.schedule(handler, str(path_to_watch), recursive=True)
    observer.start()
    print(f"Watchdog started, watching: {path_to_watch}")
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        print("Watchdog task cancelled.")
    except KeyboardInterrupt:
        print("Interrupt received; stopping watchdog.")
        observer.stop()
    finally:
        observer.stop()
        observer.join()

        print("Watchdog stopped.")


if __name__ == "__main__":
    from src.api.core import settings

    directory = settings.QUESTIONS_PATH

    asyncio.run(run_watchdog(settings.QUESTIONS_PATH))
