from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from src.ai_processing.question_topic_classification.topic_document_loader import (
    TopicDocumentLoader,
)
from src.ai_base.settings import get_settings


# For documentation for working with the database see https://python.langchain.com/docs/integrations/vectorstores/faiss/#add-items-to-vector-store
settings = get_settings()


def main(path_to_save: str):
    filepath = r"src\ai_processing\question_topic_classification\data\topic_data_description.json"
    loader = TopicDocumentLoader(filepath=filepath)
    docs = loader.load()
    embeddings = OpenAIEmbeddings(model=settings.embedding_model)
    vectorstore = FAISS.from_documents(docs, embeddings)

    vectorstore.save_local(path_to_save)


if __name__ == "__main__":
    print("Generating Vector Store")
    main(
        path_to_save=r"src\ai_processing\question_topic_classification\topic_vectorstore"
    )
