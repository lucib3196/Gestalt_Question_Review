from typing import List
from pydantic import BaseModel




class TopicDescription(BaseModel):
    name: str
    description: str
    discipline: List[str]


class FullTopicDescriptionList(BaseModel):
    topics: List[TopicDescription]


class TagAttributes(BaseModel):
    name: str
    description: str


class QuestionTagDescription(BaseModel):
    name: str
    description: str
    type: str
    returns: str
    attrs: List[TagAttributes]
    sample: str


class AllQuestionTagDescription(BaseModel):
    descriptions: List[QuestionTagDescription]
