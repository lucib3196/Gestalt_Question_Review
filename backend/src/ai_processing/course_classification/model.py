from typing import List
from pydantic import BaseModel


class FullCourseDescription(BaseModel):
    course_name: str
    course_id: str
    full_description: str
    course_level: str


class FullCourseDescriptionList(BaseModel):
    courses: List[FullCourseDescription]
