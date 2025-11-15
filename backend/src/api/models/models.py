# Standard library
from typing import List, Optional
from uuid import UUID, uuid4
from enum import Enum

# Third-party libraries
from sqlmodel import Field, Relationship, SQLModel


class QuestionTopicLink(SQLModel, table=True):
    question_id: UUID | None = Field(
        default=None, foreign_key="question.id", primary_key=True
    )
    topic_id: UUID | None = Field(
        default=None, foreign_key="topic.id", primary_key=True
    )


class QuestionLanguageLink(SQLModel, table=True):
    question_id: UUID | None = Field(
        default=None, foreign_key="question.id", primary_key=True
    )
    language_id: UUID | None = Field(
        default=None, foreign_key="language.id", primary_key=True
    )


class QuestionQTypeLink(SQLModel, table=True):
    question_id: UUID | None = Field(
        default=None, foreign_key="question.id", primary_key=True
    )
    qtype_id: UUID | None = Field(
        default=None, foreign_key="qtype.id", primary_key=True
    )


class UserRole(str, Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    DEVELOPER = "developer"
    STUDENT = "student"


class User(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    username: str | None
    email: str | None
    role: UserRole = UserRole.STUDENT
    fb_id: str | None = None
    storage_path: str | None = None
    created_questions: List["Question"] = Relationship(back_populates="created_by")


class Question(SQLModel, table=True):
    id: UUID | None = Field(default_factory=uuid4, primary_key=True, index=True)
    # Question metadata contains basic fields
    title: Optional[str] = Field(default=None, index=True)
    ai_generated: bool = False
    isAdaptive: bool = False
    topics: List["Topic"] = Relationship(
        back_populates="questions", link_model=QuestionTopicLink
    )
    languages: List["Language"] = Relationship(
        back_populates="questions", link_model=QuestionLanguageLink
    )
    qtypes: List["QType"] = Relationship(
        back_populates="questions", link_model=QuestionQTypeLink
    )

    # Storage
    local_path: Optional[str] = None
    blob_path: Optional[str] = None

    created_by_id: UUID | None = Field(default=None, foreign_key="user.id")
    created_by: Optional["User"] = Relationship(back_populates="created_questions")


class Language(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True, unique=True)

    questions: List[Question] = Relationship(
        back_populates="languages",
        link_model=QuestionLanguageLink,
    )


class QType(SQLModel, table=True):

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True, unique=True)

    questions: List[Question] = Relationship(
        back_populates="qtypes",
        link_model=QuestionQTypeLink,
    )


class Topic(SQLModel, table=True):
    __tablename__ = "topic"  # type: ignore

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    name: str = Field(index=True, unique=True)

    questions: List[Question] = Relationship(
        back_populates="topics",
        link_model=QuestionTopicLink,
    )
