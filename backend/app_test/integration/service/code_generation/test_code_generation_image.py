import io
from fastapi import UploadFile
import pytest
from pathlib import Path
from pydantic_settings import BaseSettings
from app_test.fixtures.fixture_code_generation import *
from src.api.service.ai_generation import code_generation


class TestConfig(BaseSettings):
    asset_path: Path


test_config = TestConfig(
    asset_path=Path("src/app_test/test_assets").resolve()
)


@pytest.mark.asyncio
async def test_file_upload(db_session, simple_question_text, question_manager):
    image_path = test_config.asset_path / "images" / "mass_block.png"
    contents = open(image_path, "rb").read()
    upload_file = UploadFile(filename="mass_block.png", file=io.BytesIO(contents))

    result = await code_generation.run_image(
        files=[upload_file],
        session=db_session,
        meta=simple_question_text["additional_meta"],
        qm=question_manager,
    )
    assert result["success"] is True
    assert "questions" in result
    print(result["questions"])
