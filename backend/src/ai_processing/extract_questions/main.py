import asyncio
from pathlib import Path
from typing import List

from pydantic import BaseModel, Field

from langchain.chat_models import init_chat_model
from langsmith import Client
from langgraph.graph import StateGraph, START, END

from src.pydantic_models import PageRange
from src.ai_base.multimodel_io import PDFMultiModal
from src.ai_base.settings import get_settings
from src.utils import extract_langsmith_prompt


# --- Initialization ---

# Initialize LangSmith client and project settings
client = Client()
settings = get_settings()

# Load and extract the LangSmith prompt
prompt = extract_langsmith_prompt(client.pull_prompt("generate-conceptual-questions"))

# Retrieve long-context model configuration
lcm = settings.long_context_model
if lcm is None:
    raise ValueError(
        "Long-context model (settings.long_context_model) is not configured."
    )

# Validate model parameters
model = lcm.model
provider = lcm.provider

if not model:
    raise ValueError("Invalid configuration: 'model' is missing or empty.")
if not provider:
    raise ValueError("Invalid configuration: 'provider' is missing or empty.")

# Initialize chat model
llm = init_chat_model(model=model, model_provider=provider)


class Option(BaseModel):
    text: str = Field(..., description="Text of the answer choice.")
    is_correct: bool = Field(
        ..., description="True if this option is the correct answer, otherwise False."
    )





class ConceptualQuestion(BaseModel):
    question: str = Field(..., description="The conceptual question being asked.")
    topics: List[str] = Field(
        ...,
        description="A list of three key topics or concepts that this question addresses.",
    )
    options: List["Option"] = Field(
        ...,
        description="Multiple-choice options corresponding to possible answers for the question.",
    )
    reference: "PageRange" = Field(
        ...,
        description="Page range within the lecture material where the concept or question originates.",
    )
    explanation: str = Field(
        ...,
        description="A concise explanation of the correct answer intended to help students understand the reasoning.",
    )

    def as_string(self) -> str:
        """Return a formatted string representation of the conceptual question."""
        options_formatted = "\n".join(
            [f"- {'✅ ' if opt.is_correct else ''}{opt.text}" for opt in self.options]
        )
        topics_formatted = ", ".join(self.topics)

        return (
            f"### **Conceptual Question**\n"
            f"**Question:** {self.question}\n\n"
            f"**Topics:** {topics_formatted}\n\n"
            f"**Options:**\n{options_formatted}\n\n"
            f"**Explanation:** {self.explanation}\n\n"
            f"**Reference:** {self.reference}\n"
        )


class State(BaseModel):
    lecture_pdf: str | Path
    questions: List[ConceptualQuestion] = []


async def extract_questions(state: State):
    processor = PDFMultiModal()

    class Response(BaseModel):
        derivations: List[ConceptualQuestion]

    response = await processor.ainvoke(
        prompt=prompt,
        pdf_path=state.lecture_pdf,
        output_model=Response,
        llm=llm,
    )
    return {"questions": response}


builder = StateGraph(State)
builder.add_node("extract_questions", extract_questions)

builder.add_edge(START, "extract_questions")

builder.add_edge("extract_questions", END)

graph = builder.compile()


if __name__ == "__main__":
    # Path to the lecture PDF
    pdf_path = Path(r"src\data\TransportLecture\Lecture_02_03.pdf")

    # Create graph input state
    graph_input = State(lecture_pdf=pdf_path)

    # Run the async graph and print the response
    try:
        response = asyncio.run(graph.ainvoke(graph_input))
        print("\n--- Graph Response ---")
        print(response)
    except Exception as e:
        print("\n❌ Error while running graph:")
        print(e)
