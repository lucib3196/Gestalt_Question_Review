from __future__ import annotations

# Standard library
from typing import Union
from uuid import UUID
import asyncio

# Third-party
from fastapi import HTTPException
from starlette import status
from typing import Sequence, Dict, List, Any

# Local
from src.api.database import SessionDep
from src.api.models.models import (
    Question,
)
from src.api.database import question as qdata
from src.api.core.logging import logger
from src.utils import convert_uuid
from src.api.response_models import Response



async def safe_refresh_question(question: Question, session: SessionDep):
    return qdata.safe_refresh_question(question, session)


async def create_question(
    question: Union[Question, dict], session: SessionDep
) -> Question:
    """
    Create a new Question record.

    Accepts either a `Question` model instance or a plain `dict` payload and delegates
    persistence to `question_db.create_question`. Validates input type and maps
    unexpected errors to HTTP exceptions.

    Args:
        question: The incoming question as a `Question` or `dict`.
        session: Database session dependency.

    Returns:
        The persisted `Question` instance.

    Raises:
        HTTPException: 400 if payload is invalid or creation fails with ValueError;
                       500 for unexpected errors.
    """
    if not question or (
        not isinstance(question, dict) and not isinstance(question, Question)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Question must either be object of type Question or dict or not Empty got type {type(question)}",
        )
    try:
        question = qdata.create_question(question, session)
        return question
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


async def get_all_questions(
    session: SessionDep,
    offset: int = 0,
    limit: int = 100,
) -> Sequence[Question]:
    """
    Retrieve a paginated list of Questions.

    Args:
        session: Database session dependency.
        offset: Number of records to skip.
        limit: Maximum number of records to return.

    Returns:
        A sequence of `Question` rows.

    Raises:
        HTTPException: 204 if there are no questions.
    """
    results = qdata.get_all_questions(session, offset=offset, limit=limit)
    return results


async def get_question_by_id(question_id: Union[str, UUID], session: SessionDep):
    """
    Fetch a single Question by its ID.

    Args:
        question_id: Question identifier as `str` or `UUID`.
        session: Database session dependency.

    Returns:
        The matching `Question` instance.

    Raises:
        HTTPException: 404 if not found; 400 if the ID is not a valid UUID.
    """
    try:
        results = qdata.get_question_by_id(question_id, session)
        return results
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Bad Request {str(e)}"
        )


async def delete_all_questions(session: SessionDep) -> None:
    """
    Delete all Question records.

    Args:
        session: Database session dependency.

    Returns:
        None
    """
    return qdata.delete_all_questions(session)


async def delete_question_by_id(
    question_id: Union[str, UUID], session: SessionDep
) -> Response:
    """
    Delete a Question by ID.

    Looks up the question first (raising 404 if missing), then deletes it.

    Args:
        question_id: Question identifier as `str` or `UUID`.
        session: Database session dependency.

    Returns:
        A dict with a human-readable `detail` message.

    Raises:
        HTTPException: 404 if not found; 500 for unexpected errors.
    """
    try:
        question = await get_question_by_id(question_id, session)
        if question is None:
            return Response(status=status.HTTP_200_OK, detail="Question Does Not Exist")
        qdata.delete_question_by_id(question.id, session)
        return Response(status=status.HTTP_200_OK, detail="Question Deleted")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unknown Error {str(e)}",
        )


async def edit_question_meta(
    question_id: Union[str, UUID], session: SessionDep, **kwargs
):
    """
    Update Question metadata fields.

    Delegates attribute updates to `question_db.update_question`, then returns
    the full question data (including relationships).

    Args:
        question_id: Question identifier as `str` or `UUID`.
        session: Database session dependency.
        **kwargs: Field updates to apply to the Question.

    Returns:
        A dict of the full question data from `get_question_data`.

    Raises:
        HTTPException: 500 on update failures; passes through other HTTPExceptions.
    """
    try:
        question_id = convert_uuid(question_id)
        logger.debug("These are the kwargs %s", kwargs)
        updated_question = qdata.update_question(session, question_id, **kwargs)
        return await get_question_data(question_id=updated_question.id, session=session)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating Question {question_id}: {str(e)}",
        )


async def filter_questions_meta(
    session: SessionDep, filters, **kwargs
) -> List[Dict[str, Any]]:
    """
    Filter questions by provided criteria and return full data for each match.

    Args:
        session: Database session dependency.
        **kwargs: Filter criteria supported by `question_db.filter_questions`.

    Returns:
        A list of dicts, each containing full question data.

    Raises:
        HTTPException: Propagates any HTTPExceptions from filtering or retrieval.
    """
    try:
        questions = qdata.filter_questions(session, filters, True, **kwargs)
        tasks = [
            qdata.get_question_data(question_id=r.id, session=session)
            for r in questions
        ]
        return await asyncio.gather(*tasks)
    except HTTPException as e:
        raise e


async def get_question_data(question_id: Union[str, UUID], session: SessionDep):
    """
    Retrieve a single Question's data including requested relationships.

    Args:
        question_id: Question identifier as `str` or `UUID`.
        session: Database session dependency.

    Returns:
        A dict with the question fields plus relationship arrays.

    Raises:
        HTTPException: Propagates not-found or validation errors from the DB layer.
    """
    try:
        result = await qdata.get_question_data(question_id, session)
        return result
    except HTTPException as e:
        raise e


async def get_all_question_data(session: SessionDep, limit: int = 100, offset: int = 0):
    """
    Retrieve full data for all Questions (paginated).

    Args:
        session: Database session dependency.
        limit: Maximum number of questions to fetch.
        offset: Number of questions to skip.

    Returns:
        A list of dicts, each containing full question data.

    Raises:
        HTTPException: Propagates any HTTPExceptions from the DB layer.
    """
    try:
        result = await qdata.get_all_question_data(session, limit=limit, offset=offset)
        return result
    except HTTPException as e:
        raise e
