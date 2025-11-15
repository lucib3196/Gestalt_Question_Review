import json
from typing import AsyncIterator, Iterator
from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document
import aiofiles  # type: ignore
from .model import FullCourseDescriptionList
from pathlib import Path


class CourseDocumentLoader(BaseLoader):
    def __init__(self, filepath: str | Path) -> None:
        self.file_path = Path(filepath)

    def lazy_load(self) -> Iterator[Document]:
        raw_data = json.loads(self.file_path.read_text())

        validated_data = FullCourseDescriptionList.model_validate(raw_data)
        for course in validated_data.courses:
            yield Document(
                page_content=f"Course Name: {course.course_name} Course ID: {course.course_id} \n {course.full_description}",
                metadata={
                    "source": "ucr course catalog 2019-2020",
                    "course_id": course.course_id,
                    "course_name": course.course_name,
                    "course_level": course.course_level,
                },
            )

    async def alazy_load(self) -> AsyncIterator[Document]:

        async with aiofiles.open(self.file_path, encoding="utf-8") as f:
            content = await f.read()
            full = FullCourseDescriptionList(**json.loads(content))
            for course in full.courses:
                yield Document(
                    page_content=f"Course Name: {course.course_name} Course ID: {course.course_id} \n {course.full_description}",
                    metadata={
                        "source": "ucr course catalog 2019-2020",
                        "course_id": course.course_id,
                        "course_name": course.course_name,
                        "course_level": course.course_level,
                    },
                )


if __name__ == "__main__":
    data_path = Path(
        r"src/ai_processing/course_classification/data/course_data_parsed.json"
    ).resolve()
    loader = CourseDocumentLoader(filepath=data_path)
    print("Testing Document Loader")
    for doc in loader.lazy_load():
        print()
        print(type(doc))
        print(doc)
