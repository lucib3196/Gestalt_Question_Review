# --- Standard Library ---
import json
import os
import tempfile
from datetime import date, datetime, time
from typing import Any, List, Optional, Sequence, Union
from uuid import UUID

# --- Third-Party ---
import fitz  # PyMuPDF
import pandas as pd
from IPython.display import Image, display
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_core.prompt_values import ChatPromptValue
from pydantic import BaseModel



def save_graph_visualization(
    graph,
    filename: str = "Graph.png",
    base_path: Optional[str] = None,
) -> None:
    """
    Visualizes a LangGraph StateGraph and saves it as a PNG image.

    Args:
        graph (StateGraph): The StateGraph instance to visualize.
        filename (str, optional): The filename for the saved image. Defaults to "Graph.png".
        base_path (str, optional): The directory path to save the image. If None, saves in the script's directory.
    """
    try:
        image_bytes = graph.get_graph().draw_mermaid_png()  # type: ignore
        print("Got image bites")
        display(Image(image_bytes))

        save_dir = base_path or os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(save_dir, filename)

        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "wb") as file:
            file.write(image_bytes)

        print(f"✅ Saved graph visualization at: {file_path}")
    except Exception as error:
        print(f"❌ Graph visualization failed: {error}")


async def pdf_to_image_temp(
    pdf_path: str,
    pdf_name: Optional[str] = None,
    print_summary: bool = False,
    annotate: bool = False,
) -> None:
    """
    Converts each page of a PDF into images stored in a temporary directory.

    Args:
        pdf_path (str): Path to the PDF file.
        pdf_name (str, optional): Custom name for the output images. Defaults to the PDF filename.
        print_summary (bool, optional): Whether to print a summary of generated images. Defaults to False.
    """
    pdf_document = fitz.open(pdf_path)
    pdf_name = pdf_name or os.path.splitext(os.path.basename(pdf_path))[0].replace(
        " ", "_"
    )

    summary = f"Summary\n{'*' * 25}\n"

    with tempfile.TemporaryDirectory() as tmpdir:
        for page_number in range(pdf_document.page_count):
            page: Page = pdf_document.load_page(page_number)

            page_img = f"{pdf_name}_page_{page_number + 1}.png"
            temp_path = os.path.join(tmpdir, page_img)

            pix = page.get_pixmap()  # type: ignore
            pix.save(temp_path)

            if page_number == 0:
                display(Image(filename=temp_path))

            summary += f"🖼️ Image Created: {temp_path}\n"

    if print_summary:
        print(summary)


async def pdf_to_image_persistent(
    pdf_path: str,
    persistent_directory: str,
    pdf_name: Optional[str] = None,
    print_summary: bool = False,
    annotate: bool = False,
) -> List[str]:
    """
    Converts each page of a PDF into images stored in a persistent directory.

    Args:
        pdf_path (str): Path to the PDF file.
        persistent_directory (str): Directory to save the images.
        pdf_name (str, optional): Custom name for the output images. Defaults to the PDF filename.
        print_summary (bool, optional): Whether to print a summary of generated images. Defaults to False.
    Return:
    A list of strings containing the paths to the converted images
    """
    pdf_document = fitz.open(pdf_path)
    pdf_name = pdf_name or os.path.splitext(os.path.basename(pdf_path))[0].replace(
        " ", "_"
    )
    folder_path = os.path.join(persistent_directory, pdf_name)

    summary = f"Summary\n{'*' * 25}\n"

    if os.path.exists(folder_path):
        summary += f"📁 Folder already exists at: {folder_path}\n"
    else:
        os.makedirs(folder_path, exist_ok=True)
        summary += f"📁 Folder created at: {folder_path}\n"

    image_paths = []
    for page_number in range(pdf_document.page_count):
        page = pdf_document.load_page(page_number)
        if annotate:
            # Get the page rectangle
            rect = page.rect

            # Calculate width and height
            width = rect.width
            height = rect.height
            # Get the right hand cornder
            point = (width - 25, height - 25)
            page.draw_circle(point, 25)  # type: ignore
            font_size = 30
            point = fitz.Point(point[0], point[1])
            page.insert_text(point=point, text=str(page_number), fontsize=font_size)  # type: ignore

        page_img = f"{pdf_name}_page_{page_number}.png"
        temp_path = os.path.join(folder_path, page_img)

        pix = page.get_pixmap()  # type: ignore
        pix.save(temp_path)
        image_paths.append(temp_path)

        if page_number == 0:
            display(Image(filename=temp_path))

        summary += f"🖼️ Image Created: {temp_path}\n"

    if print_summary:
        print(summary)
    return image_paths


from typing import Union


def to_serializable(obj: Any) -> Any:
    """
    Recursively convert Pydantic models (and nested dicts/lists thereof)
    into plain Python data structures.
    """
    if isinstance(obj, BaseModel):
        return obj.model_dump()
    if isinstance(obj, dict):
        return {k: to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_serializable(v) for v in obj]

    # --- Special cases ---
    if isinstance(obj, (datetime, date, time)):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)

    return obj


def parse_structured(model_class, ai_message):
    return model_class(**json.loads(ai_message.content))


def validate_column(df: pd.DataFrame, column: str):
    return column in df.columns


def validate_columns(df: pd.DataFrame, columns: list[str]):
    invalid_columns = [c for c in columns if not validate_column(df, c)]
    if invalid_columns:
        return False
    return True


def inject_message(
    messages: Union[Sequence[BaseMessage], ChatPromptValue],
    content: str,
    insert_idx: int = 0,
) -> list[BaseMessage]:
    """
    Insert a SystemMessage into a chat message sequence (or ChatPromptValue).

    - Accepts either a concrete sequence[List[BaseMessage]] or a ChatPromptValue.
    - Returns a new list with the injected SystemMessage at insert_idx.
    """
    # Convert ChatPromptValue -> list[BaseMessage]
    if isinstance(messages, ChatPromptValue):
        messages = messages.to_messages()  # <-- critical conversion
    # Ensure we can slice safely
    seq = list(messages)
    return seq[:insert_idx] + [SystemMessage(content=content)] + seq[insert_idx:]


def validate_llm_output(output: Any, model_class: type):
    if isinstance(output, dict):
        return model_class.parse_obj(output)
    elif isinstance(output, model_class):
        return output
    else:
        raise TypeError(
            f"Unexpected Resuls: Output is of type {type(output)} expected type {model_class}"
        )
