# Standard library
import json
from typing import Union, Literal
from uuid import UUID
from pathlib import Path

# Third-party
from fastapi import HTTPException
from starlette import status
import tempfile

# Local
from src.api.core.logging import logger
from src.api.database import SessionDep
from src.code_runner.run_server import run_generate
from src.utils import convert_uuid
from src.api.dependencies import QuestionManagerDependency, QuestionManager
from src.utils import convert_uuid


MAPPING_DB = {"python": "server.py", "javascript": "server.js"}
MAPPPING_FILENAME = {"python": "server.py", "javascript": "server.js"}


class CodeRunner:
    def __init__(
        self, question_id: Union[str, UUID], language: Literal["python", "javascript"]
    ):
        self.qid = convert_uuid(question_id)
        self.language = language


async def run_server(
    question_id: Union[str, UUID],
    code_language: Literal["python", "javascript"],
    session: SessionDep,
    qm: QuestionManagerDependency,
):
    mapping_db = {"python": "server.py", "javascript": "server.js"}
    mapping_filename = {"python": "server.py", "javascript": "server.js"}

    if (isinstance, str):
        question_id = convert_uuid(question_id)

    # Validate language
    if code_language not in mapping_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported code language"
        )

    try:
        response = await qm.read_file(
            question_id,
            session,
            mapping_db[code_language],
        )
        assert response
    except HTTPException:
        raise

    server_content = response.decode("utf-8")

    if isinstance(server_content, (dict, list)):
        try:
            server_content = json.dumps(server_content)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to serialize server content: {e}",
            )
    elif not isinstance(server_content, str):

        server_content = str(server_content)
    # Write to a temp file and execute

    # Try to run the file
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / mapping_filename[code_language]
            file_path.write_text(server_content, encoding="utf-8")
            logger.debug("Executing server code at %s", file_path)
            output = run_generate(str(file_path), isTesting=False)
            return output
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Execution error: {e}",
        )
