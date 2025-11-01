from __future__ import annotations

# --- Standard Library ---
import asyncio
import base64
import json
import mimetypes
from pathlib import Path
from typing import List, Literal, Union
from uuid import UUID

# --- Third-Party ---
from fastapi import HTTPException
from sqlmodel import select
from starlette import status

# --- Internal ---
from src.api.core.config import get_settings
from src.api.database import SessionDep, get_session
from src.api.models.models import Question
from src.api.response_models import (
    FileData,
    SuccessDataResponse,
    SuccessFileResponse,
    SuccessfulResponse,
)
from src.api.service.crud import question_crud as qc
from src.utils import safe_dir_name
from src.ai_workspace.utils import to_serializable


settings = get_settings()
IMAGE_MIMETYPES = {"image/png"}


def reconstruct_path(relative_path: str | Path) -> Path:
    return Path(settings.ROOT_PATH) / Path(relative_path)





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
    for m in metadata_found:
        metadata_path = base_dir / m / "metadata.json"
        content = metadata_path.read_text(encoding="utf-8")

        try:
            await create_question_full(json.loads(content), session, existing=True)
        except Exception as e:
            print(f"Failed {e}, {content}")


if __name__ == "__main__":

    async def main():
        session_gen = get_session()
        session = next(session_gen)
        try:
            _, found = check_for_new_folders(session)

        finally:
            session.close()  # finalize generator try: next(session_gen) except StopIteration: pass

    asyncio.run(main())
