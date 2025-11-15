import json
from typing import AsyncIterator, Iterator
from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document
from .models import FullTopicDescriptionList
import aiofiles
from pathlib import Path


class TopicDocumentLoader(BaseLoader):
    def __init__(self, filepath: str | Path) -> None:
        self.file_path = Path(filepath)

    def lazy_load(self) -> Iterator[Document]:
        raw_data = json.loads(self.file_path.read_text())
        validated_data = FullTopicDescriptionList.model_validate(raw_data)
        for topic in validated_data.topics:
            yield Document(
                page_content=f"Topic Name: {topic.name}\n Engineering Disciplines: {", ".join(topic.discipline)}\n Description: {topic.description}",
                metadata={
                    "source": "topic list",
                    "topic_name": {topic.name},
                    "topic_description": {topic.description},
                },
            )

    async def alazy_load(self) -> AsyncIterator[Document]:
        async with aiofiles.open(self.file_path, encoding="utf-8") as f:
            full = FullTopicDescriptionList(**json.load(f))  # type: ignore
            for topic in full.topics:
                yield Document(
                    page_content=f"Topic Name: {topic.name}\n Engineering Disciplines {topic.discipline}\n Description: {topic.description}",
                    metadata={
                        "source": "topic list",
                        "topic_name": {topic.name},
                        "topic_description": {topic.description},
                    },
                )


if __name__ == "__main__":
    filepath = r"src\ai_processing\question_topic_classification\data\topic_data_description.json"
    loader = TopicDocumentLoader(filepath=filepath)
    print("Testing Document Loader")
    for doc in loader.lazy_load():
        print()
        print(type(doc))
        print(doc)
