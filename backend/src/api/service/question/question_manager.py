# --- Standard Library ---
from pathlib import Path
from typing import Literal, Sequence, Annotated
from uuid import UUID

# --- Third-Party ---
from fastapi import HTTPException, Depends
from starlette import status

# --- Internal ---
from src.api.core import logger
from src.api.database import SessionDep
from src.api.database import question as qdb
from src.api.models.models import Question
from src.api.models.question import QuestionData, QuestionMeta
from src.api.core.config import get_settings

settings = get_settings()


class QuestionManager:
    """Manage creation, retrieval, and file operations for questions."""

    def __init__(self, session: SessionDep):
        self.session = session

    async def create_question(self, question: QuestionData | dict) -> Question:
        """Create a new question in DB and storage."""
        if not question or (
            not isinstance(question, dict) and not isinstance(question, QuestionData)
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Question must either be object of type Question or dict or not Empty got type {type(question)}",
            )
        try:
            qcreated = await qdb.create_question(question, self.session)
            return qcreated
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid or missing input when creating question: {e}",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error Processing Question Content {e}",
            )

    def get_question(
        self,
        question_id: str | UUID,
    ) -> Question:
        try:
            question = qdb.get_question(question_id, self.session)
            if not question:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Question does not exist",
                )
            return question
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Bad Request {str(e)}"
            )

    def get_all_questions(
        self, offset: int = 0, limit: int = 100
    ) -> Sequence[Question]:
        try:
            return qdb.get_all_questions(self.session, offset, limit)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Could not get questions {e}",
            )

    def delete_all_questions(self) -> bool:
        try:
            return qdb.delete_all_questions(self.session)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not delete all the question {e}",
            )

    def delete_question(self, question_id: str | UUID | None):
        try:
            return qdb.delete_question(question_id, self.session)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not delete  the question {e}",
            )

    async def update_question(
        self, question_id: str | UUID, data: QuestionData | dict
    ) -> QuestionMeta:
        """Update question metadata in the DB."""
        try:
            if isinstance(data, dict):
                data = QuestionData.model_validate(data)
            try:
                return await qdb.update_question(question_id, data, self.session)
            except Exception as e:
                logger.error(f"Failed to update question {str(e)}")
                raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Could not update question data {e}",
            )

    async def get_question_data(self, id: str | UUID | None) -> QuestionMeta:
        try:
            return await qdb.get_question_data(id, self.session)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not retrieve question data",
            )

    async def get_all_question_data(
        self, offset: int = 0, limit: int = 100
    ) -> Sequence[QuestionMeta]:
        try:
            return await qdb.get_all_question_data(self.session, offset, limit)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Could not get question data {e}",
            )

    async def filter_questions(
        self,
        filter_data: QuestionData,
    ):
        try:
            return await qdb.filter_questions(filter_data, self.session)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not filter question {e}",
            )

    def get_question_path(
        self, question_id: str | UUID | None, storage_type: Literal["cloud", "local"]
    ) -> str:
        try:
            question_path = qdb.get_question_path(
                question_id, storage_type, self.session
            )
            if not question_path:
                raise HTTPException(
                    status_code=404,
                    detail=f"Question {id} does not contain a question path set to it for {storage_type}",
                )
            return question_path
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Could not retreive question {e}",
            )

    def set_question_path(
        self,
        question_id: str | UUID | None,
        path: str | Path,
        storage_type: Literal["cloud", "local"],
    ) -> Question:
        try:
            return qdb.set_question_path(question_id, path, storage_type, self.session)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Could not set path question {e}",
            )


def get_question_manager(session: SessionDep) -> QuestionManager:
    return QuestionManager(session)


QuestionManagerDependency = Annotated[QuestionManager, Depends(get_question_manager)]
