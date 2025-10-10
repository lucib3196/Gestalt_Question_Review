import base64
from pathlib import Path
from fastapi import HTTPException
from langchain_core.prompts.chat import ChatPromptTemplate


def encode_image(image_path: str|Path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def handle_image_data(data) -> bytes:
    try:
        if isinstance(data, list):
            image_data = data[0]
            return base64.b64decode(image_data)
        else:
            raise NotImplemented
    except Exception as e:
        raise e


def write_image_data(
    image_bytes: bytes, folder_path: str | Path, filename: str
) -> bool:
    try:
        path = Path(folder_path).resolve()
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)

        save_path = path / f"{filename}"
        if save_path.suffix != ".png":
            raise ValueError(
                "Suffix allowed is only PNG either missing or nnot allowed"
            )
        with open(save_path, "wb") as f:
            f.write(image_bytes)
        return True
    except Exception as e:
        raise Exception(f"Could not save image {str(e)}")
