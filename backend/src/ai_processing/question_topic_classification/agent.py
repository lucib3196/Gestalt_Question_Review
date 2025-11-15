from pathlib import Path
from typing import Any, cast
from functools import lru_cache
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessageChunk
from langchain.tools import tool
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

from src.ai_base.settings import get_settings
from src.utils import save_graph_visualization

# Get settings
settings = get_settings()
embedding_model = settings.embedding_model
base_model = settings.base_model


# Define the model we are usiong
@lru_cache()
def load_topic_classification_resources():
    """
    Lazy-load chat model + FAISS vectorstore only when needed.
    Cached so it never reloads on every invocation.
    """
    # 1. Initialize model
    model = init_chat_model(
        settings.base_model.model,
        model_provider=settings.base_model.provider,
    )

    # 2. Resolve vectorstore path
    vector_store_path = (
        Path("src/ai_processing/question_topic_classification/topic_vectorstore")
        .resolve()
        .as_posix()
    )

    # 3. Initialize embeddings
    embeddings = OpenAIEmbeddings(model=settings.embedding_model)

    # 4. Load FAISS safely
    try:
        vectorstore = FAISS.load_local(
            vector_store_path, embeddings, allow_dangerous_deserialization=True
        )
    except Exception as e:
        raise RuntimeError(
            f"Failed to load topic classification FAISS vectorstore at "
            f"{vector_store_path}. Error: {e}"
        )

    return model, vectorstore

model, vectorstore = load_topic_classification_resources()

# Create a tool for answering based on vectorstore
@tool(response_format="content_and_artifact")
def retrieve_context(query: str):
    """Retrieve information to help answer a query."""
    retrieved_docs = vectorstore.similarity_search(query, k=2)
    serialized = "\n\n".join(
        (f"Source: {doc.metadata}\nContent: {doc.page_content}")
        for doc in retrieved_docs
    )
    return serialized, retrieved_docs


tools = [retrieve_context]

prompt_text = (
    "You have access to a tool that retrieves context from a vector store containing classification for classifiying questions"
    "Use the tool to help answer user queries."
)

agent = create_agent(model, tools, system_prompt=prompt_text)  # Pass string directly


if __name__ == "__main__":
    query = "Classify the following question A car is traveling along a straight rode at a constant speed of 50 mph what is the total distance traveled after 3 hours\n\n"

    token: AIMessageChunk
    metadata: dict[str, Any]

    folder_path = Path(r"src\ai_processing\question_topic_classification\graphs")
    save_graph_visualization(agent, folder_path, filename="agent_graph.png")

    for token_raw, metadata_raw in agent.stream(
        {"messages": [{"role": "user", "content": query}]},
        stream_mode="messages",
    ):
        token = cast(AIMessageChunk, token_raw)
        metadata = cast(dict[str, Any], metadata_raw)

        print(token.content)
