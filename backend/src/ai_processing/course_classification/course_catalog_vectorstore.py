from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from pathlib import Path
from src.ai_processing.course_classification.course_document_loader import (
    CourseDocumentLoader,
)
from src.ai_base.settings import get_settings

settings = get_settings()

# For documentation for working with the database see https://python.langchain.com/docs/integrations/vectorstores/faiss/#add-items-to-vector-store


def main(path_to_save: str):
    data_path = Path(
        r"src/ai_processing/course_classification/data/course_data_parsed.json"
    ).resolve()
    loader = CourseDocumentLoader(filepath=data_path)
    docs = loader.load()
    embeddings = OpenAIEmbeddings(model=settings.embedding_model)
    vectorstore = FAISS.from_documents(docs, embeddings)

    vectorstore.save_local(path_to_save)


if __name__ == "__main__":
    path_to_save = r"src/ai_processing/course_classification/course_catalog_index"
    print("Generating Vector Store")
    main(path_to_save)
