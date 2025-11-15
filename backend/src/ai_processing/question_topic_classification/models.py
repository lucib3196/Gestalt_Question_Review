from typing import List
from pydantic import BaseModel


class TopicDescription(BaseModel):
    name: str
    description: str
    discipline: List[str]


class FullTopicDescriptionList(BaseModel):
    topics: List[TopicDescription]
