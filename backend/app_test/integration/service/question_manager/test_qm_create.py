# --- Standard Library ---
from pathlib import Path

# --- Third-Party ---
import pytest

# --- Internal ---
from src.api.core import logger


@pytest.mark.asyncio
async def test_create_question(
    question_manager, db_session, question_payload_minimal_dict, tmp_path
):
    qcreated = await question_manager.create_question(
        question_payload_minimal_dict, db_session
    )
    assert qcreated
    assert qcreated.title == question_payload_minimal_dict["title"]
    logger.info(f"Testing QM creation this is the created question {qcreated}")

    if question_manager.storage_type == "cloud":
        expected = (
            Path("integration_test")
            / f"{question_payload_minimal_dict["title"]}_{qcreated.id}"
        )
        assert Path(qcreated.blob_name) == expected
    else:  # local
        expected = (
            Path("questions")
            / f"{question_payload_minimal_dict["title"]}_{qcreated.id}"
        )
        assert Path(qcreated.local_path) == Path(expected)
