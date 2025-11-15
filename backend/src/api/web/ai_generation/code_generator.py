from __future__ import annotations

# --- Standard Library ---
from typing import Optional, List, Sequence
import asyncio

# --- Third-Party ---
from fastapi import APIRouter, Body, HTTPException, UploadFile
from pydantic import BaseModel

# --- Internal Imports ---
from src.api.models.models import Question
from src.api.service.code_generation import run_text, run_image
from src.api.service.question.question_resource import QuestionResourceDepencency

router = APIRouter(prefix="/code_generator", tags=["code_generator"])


# Loads up directory and get all the questions
class TextGenInput(BaseModel):
    question_title: Optional[str] = None
    question: str


@router.post("/v5/text_gen")
async def generate_question_v5(
    qresource: QuestionResourceDepencency,
    data: TextGenInput = Body(..., embed=True),
) -> Sequence[Question]:

    try:
        result = await run_text(text=data.question)
        tasks = []
        for r in result:
            filedata, qdata = r
            tasks.append(qresource.create_question(qdata, filedata))
        created_questions = await asyncio.gather(*tasks)
        return created_questions
    except HTTPException as e:
        raise e


@router.post("/v5/image_gen")
async def generate_question_image_v5(
    qresource: QuestionResourceDepencency,
    files: List[UploadFile],
) -> Sequence[Question]:
    try:
        result = await run_image(
            files,
        )
        tasks = []
        for r in result:
            filedata, qdata = r
            tasks.append(qresource.create_question(qdata, filedata))
        created_questions = await asyncio.gather(*tasks)
        return created_questions
    except HTTPException as e:
        raise e
