import uuid
from uuid import UUID

import pytest
from fastapi import HTTPException


from src.api.models.models import Question
from src.api.service.crud import question_crud as qcrud_service
from app_test.fixtures.fixture_crud import *
from src.utils import *


# Only scalar fields to compare directly
SCALAR_FIELDS = {"title", "ai_generated", "isAdaptive", "createdBy", "user_id"}


# ---------------------------
# Create
# ---------------------------


@pytest.mark.asyncio
async def test_create_question_minimal(
    db_session, all_question_payloads, invalid_question_payloads
):
    # valid payloads (dict + Question model + full dict with rels)
    for payload in all_question_payloads:
        created = await qcrud_service.create_question(payload, db_session)

        # Compare scalar fields only
        if isinstance(payload, Question):
            expected = payload.model_dump(include=SCALAR_FIELDS)
        else:
            expected = {k: v for k, v in payload.items() if k in SCALAR_FIELDS}

        assert created.model_dump(include=SCALAR_FIELDS) == expected
        assert isinstance(created.id, UUID)

        # Compare relationships only when provided in a dict payload
        if not isinstance(payload, Question):
            if "topics" in payload:
                assert names(created.topics) == normset(payload["topics"])
            if "languages" in payload:
                assert names(created.languages) == normset(payload["languages"])
            if "qtype" in payload:
                # adjust if your schema uses single qtype instead of list
                assert names(created.qtypes) == normset(payload["qtype"])

    #  invalid payloads
    for bad in invalid_question_payloads:
        with pytest.raises(HTTPException) as excinfo:
            await qcrud_service.create_question(bad, db_session)
        assert excinfo.value.status_code == 400
        assert "Question must either be object of type Question or dict" in str(
            excinfo.value.detail
        )


# ---------------------------
# Read
# ---------------------------


@pytest.mark.asyncio
async def test_get_all_questions_empty(db_session):
    # When DB has no questions
    results = await qcrud_service.get_all_questions(db_session)
    assert isinstance(results, list)
    assert len(results) == 0


@pytest.mark.asyncio
async def test_get_all_questions(db_session, seed_questions, all_question_payloads):
    results = await qcrud_service.get_all_questions(db_session)
    assert len(results) == len(all_question_payloads)  # seeded 3


@pytest.mark.asyncio
async def test_get_question_by_id(db_session, question_payload_minimal_dict):
    # Not found
    assert await qcrud_service.get_question_by_id(uuid.uuid4(), db_session) is None

    # Bad UUID
    with pytest.raises(HTTPException) as excinfo:
        await qcrud_service.get_question_by_id("not-a-uuid", db_session)
    assert excinfo.value.status_code == 400
    assert "Bad Request" in str(excinfo.value.detail) or "Invalid UUID format" in str(
        excinfo.value.detail
    )

    # Happy path
    created = await qcrud_service.create_question(
        question_payload_minimal_dict, db_session
    )
    fetched = await qcrud_service.get_question_by_id(created.id, db_session)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.title == created.title == question_payload_minimal_dict["title"]


# ---------------------------
# Delete
# ---------------------------


@pytest.mark.asyncio
async def test_delete_all_questions(seed_questions, db_session):
    # Ensure seeded
    assert await qcrud_service.get_all_questions(db_session)

    # Delete all
    await qcrud_service.delete_all_questions(db_session)

    # Now empty
    retrieved = await qcrud_service.get_all_questions(db_session)

    assert retrieved == []


@pytest.mark.asyncio
async def test_delete_question_by_id(db_session, seed_questions):
    # Not found
    result = await qcrud_service.delete_question_by_id(uuid.uuid4(), db_session)
    assert ("Does Not Exist").lower() in result.detail.lower()

    # Bad UUID
    with pytest.raises(HTTPException) as excinfo:
        await qcrud_service.delete_question_by_id("bad-uuid", db_session)
    assert excinfo.value.status_code == 400
    assert "Bad Request" in str(excinfo.value.detail) or "Invalid UUID format" in str(
        excinfo.value.detail
    )

    # Delete all seeded one-by-one
    for q in await qcrud_service.get_all_questions(db_session):
        detail = await qcrud_service.delete_question_by_id(q.id, db_session)
        assert "Question Deleted" in str(detail.detail)

    # Confirm empty
    result = await qcrud_service.get_all_questions(db_session)
    assert result == []


# ---------------------------
# Update
# ---------------------------


@pytest.mark.asyncio
async def test_update_question_meta(db_session, question_payload_minimal_dict):

    created = await qcrud_service.create_question(
        question_payload_minimal_dict, db_session
    )
    qid = created.id

    # Update scalar
    updated = await qcrud_service.edit_question_meta(
        qid, session=db_session, title="New Title"
    )

    assert pick(updated, "id") == qid
    assert pick(updated, "title") == "New Title"

    # Update relationship with strings (resolve/create + attach)
    updated = await qcrud_service.edit_question_meta(
        qid, session=db_session, topics=["New Topic", " AnotherTopic  "]
    )
    assert {t.name for t in pick(updated, "topics")} == {  # type: ignore
        "new topic",
        "anothertopic",
    }
    # Scalar change persists
    assert pick(updated, "title") == "New Title"


# ---------------------------
# Filter
# ---------------------------


@pytest.mark.asyncio
async def test_filter_questions_meta(db_session, seed_questions):
    """
    Seeded data:
      - Question model instance: isAdaptive=True, ai_generated=False
      - Minimal dict:            isAdaptive=True, ai_generated=True
      - Full dict (with rels):   isAdaptive=True, ai_generated=True
    So filtering ai_generated=False should return exactly 1.
    """
    # Filter by scalar (AND across keys in your implementation)
    only_false = await qcrud_service.filter_questions_meta(
        db_session, ai_generated=False, filters=None
    )
    assert isinstance(only_false, list)
    assert len(only_false) == 1
    assert only_false[0]["ai_generated"] is False

    # Filter by title substring (case-insensitive, depends on your filter logic)
    titled = await qcrud_service.filter_questions_meta(
        db_session, title="SomeTitle", filters=None
    )
    assert all("sometitle" in q["title"].lower() for q in titled)  # type: ignore # fix:ignore

    # Filter by relationship name (expects your filter to support .any on Topic.name)
    with_topics = await qcrud_service.filter_questions_meta(
        db_session, topics=["Topic1", "topic2"], filters=None
    )
    # At least the full dict question should match (has both Topic1/Topic2); depending on OR/AND within-key,
    # this may include others. We assert that at least one has one of those topics.
    assert any(
        any(
            pick(t, "name") in {"topic1", "topic2"}
            for t in pick(q, "topics", default=[])
        )
        for q in with_topics
    )


# Get all question data
@pytest.mark.asyncio
async def test_get_question_data(seed_questions, db_session):
    # Act: fetch all questions
    results = await qcrud_service.get_all_questions(db_session)
    # Assert: at least the seeded questions exist
    assert results, "Expected at least one question from seed_questions"
    for r in results:
        # Act: get full data for each question
        response = await qcrud_service.get_question_data(r.id, db_session)
        # Basic structure checks
        assert isinstance(response, dict)
        assert "id" in response
        assert "title" in response
        assert "topics" in response
        assert "qtypes" in response
        assert "languages" in response


@pytest.mark.asyncio
async def test_get_all_question_data(seed_questions, db_session):
    results = await qcrud_service.get_all_question_data(db_session)
    assert isinstance(results, list)
    for r in results:
        assert isinstance(r, dict)
        assert "id" in r
        assert "title" in r
        assert "topics" in r
        assert "qtypes" in r
        assert "languages" in r
