# --- Standard Library ---
from typing import List
from uuid import uuid4

# --- Third-Party ---
import pytest

# --- Internal ---
from src.api.core import logger
from src.utils.test_utils import prepare_file_uploads
from src.api.response_models import FileData
from src.utils.normalization_utils import to_serializable
from src.api.response_models import (
    FileData,
)
from src.api.models.models import Question
from src.utils import normalize_content

from app_test.fixtures.fixture_crud import (
    create_question,
    retrieve_question,
    retrieve_files,
    retrieve_single_file,
)

QUESTION_KEYS = ["title", "ai_generated", "isAdaptive", "createdBy"]


# Helpers


@pytest.mark.parametrize("payload_fixture", ["question_payload_minimal_dict"])
@pytest.mark.parametrize("additional_metadata", ["", "question_additional_metadata"])
def test_question_metadata_retrieval(
    request, test_client, db_session, payload_fixture, additional_metadata
):
    """
    Integration test: create a question with optional metadata and ensure retrieval works.

    - Uses a minimal valid payload (`question_payload_minimal_dict`).
    - Runs twice: once with no metadata, and once with valid `question_additional_metadata`.
    - Valid creation should return 201 Created and allow retrieval of the created question.
    """
    # Arrange
    payload = request.getfixturevalue(payload_fixture)
    metadata = (
        request.getfixturevalue(additional_metadata) if additional_metadata else None
    )
    question = create_question(test_client, payload, metadata)
    question_id = question.id

    logger.debug("Created question body: %s", question)

    # Act: retrieve the question
    retrieved = retrieve_question(test_client, question_id)

    logger.debug("Retrieved question: %s", retrieved)
    assert retrieved

    # Assert: ensure core fields match
    data = retrieved.model_dump()
    for key in QUESTION_KEYS:
        assert data.get(key) == payload.get(key)


# File Retrieval
@pytest.mark.parametrize("file_fixture", ["file_data_payload", "question_file_payload"])
def test_list_question_files(
    request, test_client, db_session, question_payload_minimal_dict, file_fixture
):
    """
    Ensure that uploaded files for a question are listed correctly.
    """
    # Arrange: create a question with uploaded files
    files_data: List[FileData] = request.getfixturevalue(file_fixture)
    files = prepare_file_uploads(files_data)
    question = create_question(
        test_client, payload=question_payload_minimal_dict, files=files
    )
    # Act: retrieve the list of files
    validated = retrieve_files(test_client, question.id, route_arg="files")
    retrieved = validated.filepaths

    logger.debug("These are the retreived files", retrieved)
    assert len([f.filename for f in files_data]) == len(retrieved)
    assert {f.filename for f in files_data} == set(retrieved)


@pytest.mark.parametrize("file_fixture", ["file_data_payload", "question_file_payload"])
def test_list_question_files_data(
    request, test_client, db_session, question_payload_minimal_dict, file_fixture
):
    """
    Ensure that uploaded files are returned with their data (filename + content).
    """

    files_data: List[FileData] = request.getfixturevalue(file_fixture)
    files = prepare_file_uploads(files_data)

    # Create the question with attached files
    question = create_question(
        test_client,
        payload=question_payload_minimal_dict,
        files=files,
    )

    # Act
    validated = retrieve_files(test_client, question.id, route_arg="files_data")
    retrieved_files: List[FileData] = validated.filedata

    logger.debug("Retrieved file data: %s", retrieved_files)

    # Assert: Count consistency
    assert len(retrieved_files) == len(
        files_data
    ), f"Expected {len(files_data)} files, got {len(retrieved_files)}"

    # Assert: Filenames match
    uploaded_names = {f.filename for f in files_data}
    retrieved_names = {f.filename for f in retrieved_files}
    assert (
        uploaded_names == retrieved_names
    ), f"Mismatched filenames: {uploaded_names ^ retrieved_names}"

    # Assert: Content integrity
    for uploaded, retrieved in zip(
        sorted(files_data, key=lambda f: f.filename),
        sorted(retrieved_files, key=lambda f: f.filename),
    ):
        uploaded_content = normalize_content(uploaded.content)
        retrieved_content = normalize_content(retrieved.content)

        assert (
            uploaded_content == retrieved_content
        ), f"Content mismatch in file '{uploaded.filename}'"

    logger.info("File data validated successfully for %d files.", len(retrieved_files))


@pytest.mark.parametrize("file_fixture", ["file_data_payload", "question_file_payload"])
def test_read_question_file(
    request, test_client, db_session, question_payload_minimal_dict, file_fixture
):
    """
    Ensure that each uploaded file can be retrieved individually by filename.
    """
    files_data: List[FileData] = request.getfixturevalue(file_fixture)
    files = prepare_file_uploads(files_data)

    # Create the question with attached files
    question = create_question(
        test_client,
        payload=question_payload_minimal_dict,
        files=files,
    )

    # Act & Assert
    for f in files_data:
        retrieved_content = retrieve_single_file(
            test_client, question.id, filename=f.filename
        )
        assert retrieved_content == normalize_content(f.content)


def test_get_question_bad_id(test_client):
    bad_id = uuid4()
    r = test_client.get(f"/questions/{bad_id}")
    assert r.status_code == 400


def test_get_question_data_all_not_found(test_client):
    bad_id = uuid4()
    r = test_client.get(f"/questions/{bad_id}/full")
    assert r.status_code == 500


# Batch get all questions
def test_get_question_data_minimal(db_session, all_question_payloads, test_client):
    """
    Integration Test: Batch creation and retrieval of questions in minimal format.

    Steps:
    1. Create multiple questions from `all_question_payloads`.
    2. Retrieve the questions using `/questions/get_all/{offset}/{limit}/minimal`.
    3. Validate:
       - Response status code is 200.
       - Returned data is a list.
       - Each entry conforms to the `Question` schema (minimal view).
       - Count matches the number of created questions.
    """

    # --- Arrange ---
    for payload in all_question_payloads:
        serializable = to_serializable(payload)
        create_question(test_client, serializable)

    offset, limit = 0, 100

    # --- Act ---
    response = test_client.get(f"/questions/get_all/{offset}/{limit}/minimal")
    data = response.json()
    logger.debug("Retrieved minimal questions response: %s", data)

    # --- Assert: Basic response validation ---
    assert (
        response.status_code == 200
    ), f"Unexpected status code: {response.status_code}"
    assert isinstance(data, list), f"Expected list, got {type(data).__name__}"

    # --- Assert: Schema validation ---
    validated_questions = []
    for idx, q in enumerate(data):
        try:
            validated = Question.model_validate(q)
            validated_questions.append(validated)
        except Exception as e:
            pytest.fail(f"Question at index {idx} failed schema validation: {e}")

    # --- Assert: Count consistency ---
    expected_count = len(all_question_payloads)
    actual_count = len(validated_questions)
    assert (
        actual_count == expected_count
    ), f"Expected {expected_count} questions, got {actual_count}"

    logger.info(" Retrieved %d minimal questions successfully.", actual_count)


@pytest.mark.asyncio
async def test_filter_questions_no_match(test_client, create_multiple_question):
    """
    Filtering with values that should not match anything.
    Expect an empty list.
    """
    payload = {
        "title": "NonExistent",
        "ai_generated": True,
        "createdBy": "ghost_user",
    }

    response = test_client.post("/questions/filter_questions", json=payload)
    assert response.status_code == 200

    data = response.json()
    logger.info("Filter with no match response: %s", data)

    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.asyncio
async def test_question_filter_by_title(test_client, create_multiple_question):
    """
    Filter questions by a substring in the title.
    Expects at least one match from create_multiple_questions fixture.
    """
    payload = {"title": "SomeTitle"}

    response = test_client.post("/questions/filter_questions", json=payload)
    assert response.status_code == 200

    data = response.json()
    logger.info("Filter by title response: %s", data)

    assert isinstance(data, list)
    assert len(data) > 0
    for q in data:
        assert "title" in q
        assert payload["title"].lower() in q["title"].lower()


@pytest.mark.asyncio
async def test_filter_questions_by_title_and_flags(
    test_client, create_multiple_question
):
    """
    Filters by a substring in title + ai_generated + createdBy.
    Uses the questions inserted by the create_multiple_questions fixture.
    """
    payload = {
        "title": "Thermodynamics",
        "ai_generated": False,
        "createdBy": "tester_thermo",
    }

    response = test_client.post("/questions/filter_questions", json=payload)
    assert response.status_code == 200

    data = response.json()
    logger.info("Filter by title + flags response: %s", data)

    assert isinstance(data, list)
    assert len(data) >= 1

    for q in data:
        assert payload["title"].lower() in q["title"].lower()
        assert q["ai_generated"] == payload["ai_generated"]
        assert q["createdBy"] == payload["createdBy"]


# # Misc
# @pytest.mark.parametrize("payload_fixture", ["question_payload_minimal_dict"])
# @pytest.mark.parametrize("file_fixture", ["file_data_payload", "question_file_payload"])
# @pytest.mark.parametrize("additional_metadata", ["", "question_additional_metadata"])
# def test_question_metadata_retrieval_full(
#     request, test_client, db_session, payload_fixture, additional_metadata, file_fixture
# ):
#     """
#     Integration test: create a question with optional metadata and ensure retrieval works.

#     - Uses a minimal valid payload (`question_payload_minimal_dict`).
#     - Runs twice: once with no metadata, and once with valid `question_additional_metadata`.
#     - Valid creation should return 201 Created and allow retrieval of the created question.
#     """
#     # Arrange
#     payload = request.getfixturevalue(payload_fixture)
#     metadata = (
#         request.getfixturevalue(additional_metadata) if additional_metadata else None
#     )
#     files_data = request.getfixturevalue(file_fixture)
#     files = prepare_file_uploads(files_data)

#     data = {"question": json.dumps(payload)}
#     if metadata:
#         data["additional_metadata"] = json.dumps(metadata)

#     # Act: create the question
#     create_resp = test_client.post("/questions/", data=data, files=files)
#     assert create_resp.status_code == 201, create_resp.text
#     body = create_resp.json()
#     question_id = body["question"]["id"]

#     logger.debug("Created question body: %s", body)

#     # Act: retrieve the question
#     retrieved_resp = test_client.get(f"/questions/{question_id}/full")
#     assert retrieved_resp.status_code == 200, retrieved_resp.text

#     retrieved_body = retrieved_resp.json()
#     retrieved_question = retrieved_body["question"]

#     retrieved_filesdata = retrieved_body["files"]

#     logger.debug("Retrieved question: %s", retrieved_question)

#     # Assert: ensure core fields match
#     assert retrieved_question
#     for key in QUESTION_KEYS:
#         assert retrieved_question.get(key) == payload.get(key)

#     assert retrieved_filesdata
#     retrieved_filenames = {f["filename"] for f in retrieved_filesdata}
#     expected_filenames = {f.filename for f in files_data}
#     assert retrieved_filenames == expected_filenames
