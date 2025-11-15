from pathlib import Path
from src.data_parser import pdf_page_to_image_bytes
from src.ai_base.multimodel_io import pdf_multimodal
from src.ai_base.settings import get_settings
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field
from typing import List, Tuple

pdf_path = Path(r"src\data\TransportLecture\Lecture_02_03.pdf")
pdf_bytes = pdf_page_to_image_bytes(pdf_path)

# LLM Set Up
settings = get_settings()
llm = init_chat_model(
    settings.base_model.model, model_provider=settings.base_model.provider
)


class PageRange(BaseModel):
    start_page: int = Field(..., description="Starting page of the section")
    end_page: int = Field(..., description="Ending page of the section")


class SectionBreakdown(BaseModel):
    contains: bool = Field(
        ..., description="Whether it contains the section we are looking for"
    )
    sections: List[PageRange] = Field(
        default_factory=list,
        description="List of page ranges of interest (each containing start_page and end_page)",
    )


class Response(BaseModel):
    lecture_title: str = Field(
        ..., description="A consise title of what the lecture covers"
    )
    lecture_summary: str = Field(
        ...,
        description="A consise and to the point description of what the lecture covers",
    )
    conceptual_questions: List[str] = Field(
        ...,
        description="Generate up to 3 conceptual questions based on the lecture material",
    )
    derivations: SectionBreakdown = Field(
        ..., description="Wheter the content material contains derivations"
    )
    computational_problems: SectionBreakdown = Field(
        ...,
        description="Wether the lecture content contains any computational questions",
    )


prompt = """
You are an assistant designed to analyze lecture materials (PDFs or images of lecture notes) and extract their essential educational content.

Your task is to produce a concise and structured summary containing:

Lecture Title — A short, clear title summarizing the topic or central concept of the lecture.

Lecture Summary — A paragraph-length description explaining what the lecture covers and its main ideas.

Conceptual Questions — Up to 3 thoughtful, open-ended questions that test understanding of key principles rather than computation.

Derivations — Whether the lecture contains derivations (step-by-step equation developments), along with their page ranges.

Computational Problems — Whether the lecture includes numerical examples or calculations, along with their page ranges.

Your output should follow the schema provided, accurately reflecting the lecture’s educational structure and contents.

A derivation refers to any step-by-step mathematical development or logical formulation of an equation, principle, or relationship within the lecture material.

When identifying derivations, look for:
• Sequences of equations that follow from one another (e.g., applying physical laws or mathematical identities).
• Explanations that start from general laws and arrive at specific formulas.
• Use of differential or integral operations, simplifications, or substitutions.

Return whether derivations are present, and if so, provide the page ranges where these appear.


A computational problem refers to any worked-out numerical or quantitative example within the lecture material.

These usually involve substituting numerical values into equations, calculating results, or solving for an unknown variable.

Look for indicators such as “Given,” “Find,” “Calculate,” “Determine,” or numeric examples demonstrating application of a concept.

Return whether computational problems are present, and if so, specify the corresponding page ranges.
"""

response = pdf_multimodal(
    "What is in the lecture", llm, pdf_path, output_model=Response
)
print(response)
