# --- Standard Library ---
import json

# --- Third-Party ---
import pytest

# --- Internal ---
from src.api.core import logger
from src.utils import pick
from src.utils.test_utils import prepare_file_uploads
from fastapi.encoders import jsonable_encoder


# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
# Keys of interest for minimal question validation
QUESTION_KEYS = ["title", "ai_generated", "isAdaptive", "createdBy"]
ADDTIONAL_METAKEYS = ["topics", "languages", "qtypes"]


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def validate_response_payload(payload: dict, created: dict, key: str) -> bool:
    """Compare a given key in the request payload and response payload."""
    return pick(payload, key) == pick(created, key)


# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------
def test_create_question_response(
    create_question_minimal_response, question_payload_minimal_dict
):
    """Ensure a valid question payload creates a question successfully."""
    resp = create_question_minimal_response
    body = resp.json()
    logger.debug("This is the body %s", body)

    assert resp.status_code == 201
    qcreated = body["question"]

    # Validate core keys
    assert qcreated
    for k in QUESTION_KEYS:
        assert validate_response_payload(question_payload_minimal_dict, qcreated, k)


def test_create_question_bad_response(create_question_bad_payload_response):
    """Ensure an invalid payload returns a 400 error with proper message."""
    resp = create_question_bad_payload_response
    body = resp.json()

    assert resp.status_code == 400
    assert "Invalid or missing input when creating question" in body["detail"]


@pytest.mark.parametrize(
    "payload_fixture", ["question_payload_minimal_dict", "qpayload_bad"]
)
@pytest.mark.parametrize("file_fixture", ["file_data_payload", "question_file_payload"])
@pytest.mark.parametrize("additional_metadata", ["", "question_additional_metadata"])
def test_create_question_with_files(
    request, test_client, db_session, payload_fixture, file_fixture, additional_metadata
):
    """
    Integration test for creating a question with file uploads and optional metadata.

    - Uses both valid (`question_payload_minimal_dict`) and invalid (`qpayload_bad`) payloads.
    - Includes two file fixtures for variety in uploaded content.
    - Optionally adds extra metadata to test richer input handling.
    - Verifies:
      * 201 response and key consistency for valid payloads.
      * Proper handling of topics, languages, and qtypes when metadata is present.
      * Error responses (400/422/500) for invalid payloads.
    """
    # --- Arrange ---
    payload = request.getfixturevalue(payload_fixture)
    files_data = request.getfixturevalue(file_fixture)
    files = prepare_file_uploads(files_data)

    metadata = (
        request.getfixturevalue(additional_metadata) if additional_metadata else None
    )

    data = {"question": json.dumps(payload)}
    if metadata:
        data["additional_metadata"] = json.dumps(metadata)

    # --- Act ---
    resp = test_client.post("/questions/", data=data, files=files)
    body = resp.json()
    logger.debug("Response body: %s", body)

    # --- Assert ---
    if payload_fixture == "question_payload_minimal_dict":
        # Success case
        assert resp.status_code == 201
        qcreated = body["question"]
        assert qcreated

        # Validate base keys
        for k in QUESTION_KEYS:
            assert validate_response_payload(payload, qcreated, k)

        # Validate metadata if provided
        if metadata:
            # Topics
            if metadata.get("topics"):
                response_topics = [
                    t["name"] if isinstance(t, dict) else t
                    for t in qcreated.get("topics", [])
                ]
                for topic in metadata["topics"]:
                    assert topic.lower() in [rt.lower() for rt in response_topics]

            # Languages
            if metadata.get("languages"):
                response_languages = [
                    l["name"] if isinstance(l, dict) else l
                    for l in qcreated.get("languages", [])
                ]
                for lang in metadata["languages"]:
                    assert lang.lower() in [rl.lower() for rl in response_languages]

            # Qtypes
            if metadata.get("qtypes"):
                response_qtypes = [
                    q["name"] if isinstance(q, dict) else q
                    for q in qcreated.get("qtypes", [])
                ]
                for qt in metadata["qtypes"]:
                    assert qt.lower() in [rq.lower() for rq in response_qtypes]

    else:
        # Failure case
        assert resp.status_code in (400, 422, 500)


@pytest.mark.parametrize("file_fixture", ["file_data_payload", "question_file_payload"])
def test_create_question_minimal_with_files(
    request, test_client, question_payload_minimal_dict, file_fixture
):
    """Ensure a minimal valid payload with files creates a question successfully."""
    files_data = request.getfixturevalue(file_fixture)
    files = prepare_file_uploads(files_data)

    resp = test_client.post(
        "/questions/",
        data={"question": json.dumps(question_payload_minimal_dict)},
        files=files,
    )

    assert resp.status_code == 201
    body = resp.json()
    qcreated = body["question"]

    # Validate required keys
    for k in QUESTION_KEYS:
        assert qcreated.get(k) == question_payload_minimal_dict.get(k)


def test_create_question_invalid_payload(test_client, qpayload_bad, file_data_payload):
    """Invalid payload should fail with 400/422/500."""
    files = prepare_file_uploads(file_data_payload)

    resp = test_client.post(
        "/questions/", data={"question": json.dumps(qpayload_bad)}, files=files
    )

    assert resp.status_code in (400, 422, 500)


def test_create_question_with_topics(
    test_client,
    question_payload_minimal_dict,
    question_additional_metadata,
    file_data_payload,
):
    """Check that topics metadata is saved correctly."""
    files = prepare_file_uploads(file_data_payload)

    data = {
        "question": json.dumps(question_payload_minimal_dict),
        "additional_metadata": json.dumps(
            {"topics": question_additional_metadata["topics"]}
        ),
    }
    resp = test_client.post("/questions/", data=data, files=files)
    assert resp.status_code == 201

    qcreated = resp.json()["question"]

    response_topics = [
        t["name"] if isinstance(t, dict) else t for t in qcreated.get("topics", [])
    ]
    for topic in question_additional_metadata["topics"]:
        assert topic.lower() in [rt.lower() for rt in response_topics]


def test_create_question_with_languages(
    test_client,
    question_payload_minimal_dict,
    question_additional_metadata,
    file_data_payload,
):
    """Check that languages metadata is saved correctly."""
    files = prepare_file_uploads(file_data_payload)

    data = {
        "question": json.dumps(question_payload_minimal_dict),
        "additional_metadata": json.dumps(
            {"languages": question_additional_metadata["languages"]}
        ),
    }
    resp = test_client.post("/questions/", data=data, files=files)
    assert resp.status_code == 201

    qcreated = resp.json()["question"]

    response_languages = [
        l["name"] if isinstance(l, dict) else l for l in qcreated.get("languages", [])
    ]
    for lang in question_additional_metadata["languages"]:
        assert lang.lower() in [rl.lower() for rl in response_languages]


def test_create_question_with_qtypes(
    test_client,
    question_payload_minimal_dict,
    question_additional_metadata,
    file_data_payload,
):
    """Check that qtypes metadata is saved correctly."""
    files = prepare_file_uploads(file_data_payload)

    data = {
        "question": json.dumps(question_payload_minimal_dict),
        "additional_metadata": json.dumps(
            {"qtypes": question_additional_metadata["qtype"]}
        ),
    }
    resp = test_client.post("/questions/", data=data, files=files)
    assert resp.status_code == 201

    qcreated = resp.json()["question"]

    response_qtypes = [
        q["name"] if isinstance(q, dict) else q for q in qcreated.get("qtypes", [])
    ]
    for qt in question_additional_metadata["qtype"]:
        assert qt.lower() in [rq.lower() for rq in response_qtypes]


def test_create_multiple_questions(test_client, all_question_payloads):
    """Ensure multiple question payloads can be created sequentially."""
    for p in all_question_payloads:
        data = {"question": json.dumps(p)}
        response = test_client.post("/questions/", data=data)
        assert response.status_code == 201
