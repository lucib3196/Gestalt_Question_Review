# --- Standard Library ---
from typing import Optional, Type

# --- Third-Party ---
from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage
from openai import OpenAI
from pydantic import BaseModel
from .base_models import BaseOutput
from typing import Union

# --- Internal ---
from src.ai_base.settings import ai_settings
from src.utils import encode_image


client = OpenAI()

MODEL = ai_settings.MODEL
MODEL_PROVIDER = ai_settings.PROVIDER


def langchain_multimodal(
    prompt: str,
    image_data: str,
    llm: BaseChatModel,
    output_model: Optional[Type[BaseModel]] = BaseOutput,
) -> Union[dict, BaseModel]:
    """
    Generate a multimodal response using a LangChain-compatible language model.

    This function sends both text and image inputs to an LLM that supports multimodal
    (text + image) understanding. It optionally returns structured output conforming
    to a given Pydantic model schema.

    Args:
        prompt (str): The textual prompt or question for the LLM.
        image_data (str): The base64-encoded image data (JPEG/PNG) to include as input.
        llm (BaseChatModel): A LangChain chat model instance that supports multimodal input.
        output_model (Optional[Type[BaseModel]]): A Pydantic model class defining the expected
            structured output. Defaults to `BaseOutput`. If `None`, the model returns free-form text.

    Returns:
        Any: The LLM’s response. Either a structured Pydantic model (if `output_model` is provided)
        or a raw LLM text response.

    """
    # Build content blocks that the model supports
    content_blocks = [
        {"type": "text", "text": prompt},
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
        },
    ]

    # Create the human message properly
    human_msg = HumanMessage(content=content_blocks)

    if output_model:
        chain = llm.with_structured_output(schema=output_model)
        return chain.invoke([human_msg])
    else:
        return llm.invoke([human_msg])


def openai_multimodal(
    prompt: str, base64_image: str, response_model: Type[BaseModel] = BaseOutput
) -> str | None:
    """
    Generate a multimodal response using the OpenAI API.

    This function sends a text prompt and an image (as a base64-encoded JPEG) to
    an OpenAI multimodal model (e.g., `gpt-4.1`) and returns a structured or text-based response.

    Args:
        prompt (str): The textual prompt or question for the model.
        image_path (str): The base64-encoded image data (JPEG/PNG) to include as input.
        response_model: The expected output schema (Pydantic model or `response_format` object).

    Returns:
        str | dict: The parsed message content from the model's response. This may be
        a structured JSON object if a schema was provided.
    """
    completion = client.chat.completions.parse(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                        },
                    },
                ],
            }
        ],
        response_format=response_model,
    )
    return completion.choices[0].message.content


if __name__ == "__main__":
    from pathlib import Path

    model = init_chat_model(MODEL, model_provider=MODEL_PROVIDER)
    test_image = Path(r"backend\assets\images\mass_block.png").resolve()
    base_prompt = "What is in the image"

    response = langchain_multimodal(base_prompt, encode_image(test_image), llm=model)
    response = openai_multimodal(
        base_prompt,
        encode_image(test_image),
    )
