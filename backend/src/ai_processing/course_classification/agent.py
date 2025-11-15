from pathlib import Path
from typing import Any, cast

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessageChunk
from langchain.tools import tool
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.agents.middleware import wrap_tool_call
from langchain_core.messages import ToolMessage

from src.ai_base.settings import get_settings
from src.utils import save_graph_visualization

# Get settings
settings = get_settings()
embedding_model = settings.embedding_model
base_model = settings.base_model

# Define the model we are usiong
model = init_chat_model(base_model.model, model_provider=base_model.provider)
# Load in vector store
vector_store_path = (
    Path("src/ai_processing/course_classification/course_catalog_index")
    .resolve()
    .as_posix()
)
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
vectorstore = FAISS.load_local(
    vector_store_path, embeddings, allow_dangerous_deserialization=True
)


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


# @wrap_tool_call
# def handle_tool_errors(request, handler):
#     """Handle tool execution errors with custom messages."""
#     try:
#         return handler(request)
#     except Exception as e:
#         # Return a custom error message to the model
#         return ToolMessage(
#             content=f"Tool error: Please check your input and try again. ({str(e)})",
#             tool_call_id=request.tool_call["id"],
#         )


tools = [retrieve_context]

prompt_text = (
    "You have access to a tool that retrieves context from a blog post. "
    "Use the tool to help answer user queries."
)

agent = create_agent(
    model,
    tools,
    system_prompt=prompt_text,
)


if __name__ == "__main__":
    query = "What course is offered by UCR for mechanical engineering that is focused on thermodynamics and heat transfer\n\n"

    token: AIMessageChunk
    metadata: dict[str, Any]

    folder_path = Path("src/ai_processing/course_classification/graphs")
    save_graph_visualization(agent, folder_path, filename="agent_graph.png")

    for token_raw, metadata_raw in agent.stream(
        {"messages": [{"role": "user", "content": query}]},
        stream_mode="messages",
    ):
        token = cast(AIMessageChunk, token_raw)
        metadata = cast(dict[str, Any], metadata_raw)

        node = metadata["langgraph_node"]
        print(f"node: {node}")
        print(f"content: {token.content}")
