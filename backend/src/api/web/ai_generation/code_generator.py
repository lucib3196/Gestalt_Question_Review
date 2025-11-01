from __future__ import annotations

# --- Standard Library ---
from typing import Optional, List

# --- Third-Party ---
from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel

# --- Internal ---
from src.api.database.database import get_session
from src.api.service.ai_generation.code_generation import run_text, run_image
from fastapi import UploadFile
from src.api.dependencies import QuestionManagerDependency

router = APIRouter(prefix="/codegenerator", tags=["code_generator"])


# Loads up directory and get all the questions
class TextGenInput(BaseModel):
    question_title: Optional[str] = None
    question: str


@router.post("/v5/text_gen")
async def generate_question_v5(
    qm: QuestionManagerDependency,
    data: TextGenInput = Body(..., embed=True),
    # current_user=Depends(user.get_current_user),
    session=Depends(get_session),
):
    # user_id = await user.get_user_by_name(
    #     username=current_user.username,
    #     email=current_user.email,
    #     session=session,
    # )
    # if not user_id:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Must be logged in to use generation",
    #     )
    additional_meta = {
        # "createdBy": current_user.email,
        # "user_id": user_id,
        "title": data.question_title
        or None,
    }
    try:
        return await run_text(
            text=data.question, session=session, additional_meta=additional_meta, qm=qm
        )
    except HTTPException as e:
        raise e


@router.post("/v5/image_gen")
async def generate_question_image_v5(
    qm: QuestionManagerDependency,
    files: List[UploadFile],
    # current_user=Depends(user.get_current_user),
    session=Depends(get_session),
):
    # user_id = await user.get_user_by_name(
    #     username=current_user.username,
    #     email=current_user.email,
    #     session=session,
    # )
    # if not user_id:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Must be logged in to use generation",
    #     )
    # additional_meta = {
    #     "createdBy": current_user.email,
    #     "user_id": user_id,
    # }
    try:
        return await run_image(
            files,
            session,
            qm=qm,
            # meta=additional_meta,
        )
    except HTTPException as e:
        raise e
