# --- Standard Library ---
from typing import List

# --- Third-Party ---
import pytest

# --- Internal ---
from src.utils.test_utils import prepare_file_uploads
from src.api.response_models import FileData
from app_test.fixtures.fixture_crud import (
    create_question,
    retrieve_single_file,
)
from src.utils import to_serializable, normalize_content


@pytest.mark.parametrize("file_fixture", ["file_data_payload", "question_file_payload"])
def test_update_file(
    request, test_client, db_session, question_payload_minimal_dict, file_fixture
):
    """
    Ensure that uploaded files for a question can be updated (overwritten)
    and that the new content is retrievable.
    """
    # Arrange: create a question with uploaded files
    files_data: List[FileData] = request.getfixturevalue(file_fixture)
    files = prepare_file_uploads(files_data)

    # Create the question with attached files
    question = create_question(
        test_client,
        payload=question_payload_minimal_dict,
        files=files,
    )

    # Act + Assert: update each file and verify new content
    for f in files_data:
        new_content = f"Updated content for {f.filename}"
        update_payload = {
            "question_id": to_serializable(question.id),
            "filename": f.filename,
            "new_content": new_content,
        }

        update_resp = test_client.put("/questions/update_file", json=update_payload)
        assert update_resp.status_code == 200, update_resp.text

        # Retrieve the updated file
        retrieved_content = retrieve_single_file(test_client, question.id, f.filename)
        assert retrieved_content == normalize_content(new_content)


@pytest.mark.asyncio
async def test_update_question_meta_title_and_isadaptive(
    test_client, question_payload_minimal_dict
):
    """
    Creates a single question, then PATCHes metadata (title, isAdaptive).
    Verifies the route returns the updated object.
    """
    question = create_question(test_client, question_payload_minimal_dict)

    # 2) Patch its metadata
    updates = {
        "title": "Updated Title",
        "isAdaptive": True,
    }
    patch_resp = test_client.patch(
        f"/questions/update_question/{question.id}",
        json=updates,
    )
    assert patch_resp.status_code == 200

    updated = patch_resp.json()
    # Depending on your edit_question_meta return shape, this may be a dict with the fields
    assert updated["id"] == str(question.id)
    assert updated["title"] == "Updated Title"
    assert updated["isAdaptive"] is True
