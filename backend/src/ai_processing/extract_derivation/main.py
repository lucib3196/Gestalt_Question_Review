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
prompt = extract_langsmith_prompt(client.pull_prompt("extract-derivations"))

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


class Derivation(BaseModel):
    derivation_title: str = Field(
        ...,
        description="A short, concise title describing what the derivation focuses on.",
    )
    derivation_stub: str = Field(
        ...,
        description="A brief statement of the equation, relationship, or expression being derived.",
    )
    steps: List[str] = Field(
        ...,
        description="An ordered list of logical or mathematical steps used to carry out the derivation.",
    )
    reference: PageRange = Field(
        ...,
        description="The range of pages within the lecture material where this derivation appears.",
    )

    def as_string(self) -> str:
        steps_formatted = "\n".join(
            [f"{i+1}. {step}" for i, step in enumerate(self.steps)]
        )
        return (
            f"### **{self.derivation_title}**\n"
            f"**Stub:** {self.derivation_stub}\n\n"
            f"**Steps:**\n{steps_formatted}\n\n"
            f"**Reference:** {self.reference}\n"
        )


class State(BaseModel):
    lecture_pdf: str | Path
    derivations: List[Derivation] = []


async def extract_derivations(state: State):
    processor = PDFMultiModal()

    class Response(BaseModel):
        derivations: List[Derivation]

    response = await processor.ainvoke(
        prompt=prompt,
        pdf_path=state.lecture_pdf,
        output_model=Response,
        llm=llm,
    )
    return {"derivations": response}


builder = StateGraph(State)
builder.add_node("extract_derivations", extract_derivations)

builder.add_edge(START, "extract_derivations")

builder.add_edge("extract_derivations", END)

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
