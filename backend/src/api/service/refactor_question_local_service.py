from __future__ import annotations

# --- Standard Library ---
import asyncio
from pathlib import Path
import json

# --- Third-Party ---
from sqlmodel import select
from src.utils import pick

# --- Internal ---
from src.api.core.config import get_settings
from src.api.database import SessionDep, get_session
from src.api.models.models import Question
from src.api.service import refactor_question_storage_service as qs
from src.api.service.crud import question_crud as qc
from src.utils import normalize_kwargs
from fastapi import HTTPException
from src.api.core import logger
from src.api.response_models import FileData
from src.utils import convert_uuid
from src.utils import normalize_timestamps
from src.ai_workspace.utils import to_serializable

settings = get_settings()
async def read_file_async(path: Path) -> str:
    loop = asyncio.get_running_loop()
    # offload file IO
    return await loop.run_in_executor(None, path.read_text, "utf-8")


def check_for_new_folders(session: SessionDep):
    base_dir = Path(settings.QUESTIONS_PATH).resolve()

    all_q = session.exec(select(Question)).all()
    db_folders = {
        parts[1]
        for q in all_q
        if q.local_path and (parts := str(q.local_path).split("/")) and len(parts) > 1
    }
    disk_folders = {p.name for p in base_dir.iterdir() if p.is_dir()}

    new_folders = disk_folders - db_folders

    metadata_not_found = []
    metadata_found = []
    for folder in new_folders:
        metadata_path = base_dir / folder / "metadata.json"
        if not metadata_path.exists():
            metadata_not_found.append(folder)
        else:
            metadata_found.append(folder)

    return metadata_not_found, metadata_found


async def handle_metadata_found(metadata_found: list[str], session: SessionDep):
    base_dir = Path(settings.QUESTIONS_PATH).resolve()
    created_count = 0
    updated_count = 0

    for m in metadata_found:
        metadata_path = base_dir / m / "metadata.json"

        # If file missing, skip
        if not metadata_path.exists():
            print(f"metadata.json not found for {m}, skipping")
            continue

        try:
            content = json.loads(metadata_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"Failed to read/parse metadata.json for {m}: {e}")
            continue
        question_id = content.get("id", None)
        exists = False

        # Check existence in DB
        if question_id:
            try:
                question_id = convert_uuid(question_id)
                await qc.get_question_by_id(question_id, session=session)
                exists = True
            except HTTPException as e:
                if e.status_code == 404:
                    exists = False
                    print("Not a question")
                else:
                    print(f"Error checking question id {question_id} for {m}: {e}")
                    continue

        try:
            if not exists:
                # CREATE
                q, qdata = await qs.create_question_full(
                    content, session, existing=True
                )
                question_id = q.id
                created_count += 1
                print(f"Created question for metadata {m} with new ID {question_id}")
                metadata = qdata
            else:
                # UPDATE
                for field in ["id", "created_at", "updated_at"]:
                    content.pop(field, None)
                qdata = await qc.edit_question_meta(
                    question_id=question_id,
                    session=session,
                    **normalize_kwargs(content),
                )
                updated_count += 1
                print(f"Updated question id {question_id} from metadata {m}")
                metadata = qdata

            # --- Rewrite metadata.json ---
            print("This is the metdata before", metadata)
            metadata = FileData(
                filename="metadata.json",
                content=to_serializable(normalize_timestamps(metadata)),
            )
            await qs.write_files_to_directory(
                question_id=question_id,
                files_data=[metadata],
                session=session,
            )
            print(f"Rewrote metadata.json for {question_id}")

        except Exception as e:
            print(f"Failed to process {m}: {e}, content: {content}")
            continue

    # Final summary
    print(
        f"Summary: {created_count} questions created, {updated_count} questions updated."
    )


if __name__ == "__main__":

    async def main():
        session_gen = get_session()
        session = next(session_gen)
        try:
            _, found = check_for_new_folders(session)
            await handle_metadata_found(found, session)

        finally:
            session.close()  # finalize generator try: next(session_gen) except StopIteration: pass

    asyncio.run(main())
