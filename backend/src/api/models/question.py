from pydantic import BaseModel
from typing import List


class QuestionMeta(BaseModel):
    title: str
    ai_generated: bool
    isAdaptive: bool
    topics: List[str]
    languages: List[str]
    qtypes: List[str]


class QRelationshipData(BaseModel):
    topics: List[str]
    qtypes: List[str]
    languages: List[str]
