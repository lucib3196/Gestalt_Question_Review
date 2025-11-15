# Standard library
import tempfile
from pathlib import Path
from typing import Literal
from uuid import UUID

# Third-party libraries
from fastapi import APIRouter, HTTPException
from starlette import status

# Local application imports
from src.api.core import logger
from src.api.database import SessionDep
from src.api.service.question.question_manager import QuestionManagerDependency
from src.code_runner.models import CodeRunException, CodeRunResponse, QuizData
from src.code_runner.runtime_switcher import run_generate
from src.api.service.storage_manager import StorageDependency
from src.api.dependencies import StorageTypeDep

router = APIRouter(prefix="/run_server", tags=["code_running", "questions"])

MAPPING_DB = {"python": "server.py", "javascript": "server.js"}
MAPPPING_FILENAME = {"python": "server.py", "javascript": "server.js"}


@router.post("/{qid}/{server_language}", response_model=QuizData)
async def run_server(
    qid: str | UUID,
    server_language: Literal["python", "javascript"],
    qm: QuestionManagerDependency,
    storage: StorageDependency,
    storage_type: StorageTypeDep,
) -> QuizData:
    if server_language not in MAPPPING_FILENAME:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported language: {server_language}",
        )

    server_file = MAPPPING_FILENAME[server_language]

    try:
        question = qm.get_question(qid)
        question_path = qm.get_question_path(question.id, storage_type)
        resolved_path = storage.get_storage_path(str(question_path), relative=False)
        files = storage.list_files(resolved_path)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error resolving question storage path")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error accessing question storage path",
        ) from e

    if server_file not in files:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question does not contain file {server_file}",
        )

    server_path = Path(resolved_path) / server_file

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir) / server_file
            data = server_path.read_bytes()
            if data is None:
                raise FileNotFoundError(f"File data is None {server_path}")
            tmp_path.write_bytes(data)
            run_response: CodeRunResponse = run_generate(
                tmp_path, server_language, isTesting=False
            )
    except CodeRunException:
        raise
    except Exception as e:
        logger.exception("Error running server file")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error running {server_language} file {server_file}: {str(e)}",
        ) from e

    if not run_response.quiz_response:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Code ran successfully but quiz data is None",
        )

    return run_response.quiz_response
