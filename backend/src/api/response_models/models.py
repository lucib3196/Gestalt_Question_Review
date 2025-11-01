# --- Standard Library ---
from pathlib import Path
from typing import Any, List, Optional, Union
from uuid import UUID

# --- Third-Party ---
from pydantic import BaseModel, Field

# --- Internal ---
from src.api.models.question import QuestionMeta


class FileData(BaseModel):
    filename: str
    content: dict | str | Any


class FilesData(BaseModel):
    files: List[FileData]


class SuccessfulResponse(BaseModel):
    """Base success response shared by all API responses."""

    status: int  # keep this strict (HTTP status codes are int)
    detail: str


class SuccessDataResponse(SuccessfulResponse):
    """Success response with a file system path included."""

    data: Union[str, bytes, None]


class SuccessFileResponse(SuccessfulResponse):
    """Success response with one or more file objects."""

    filedata: List[FileData] = Field(
        default_factory=list,
        description="List of file objects or file strings",
    )
    filepaths: List[str] | List[Path] = Field(
        default_factory=list,
        description="List of relative file paths",
    )

    class Config:
        populate_by_name = True  # allows using both aliases & python names


class Response(BaseModel):
    status: int
    detail: str


class QuestionReadResponse(BaseModel):
    status: int
    question: QuestionMeta
    files: List[FileData] | List[str] = []
    detail: str


class UpdateFile(BaseModel):
    question_id: str | UUID
    filename: str
    new_content: str | dict


class AdditionalQMeta(BaseModel):
    topics: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    qtype: Optional[List[str]] = None
