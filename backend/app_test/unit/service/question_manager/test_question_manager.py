# Stdlib
import uuid
from pathlib import Path
from src.api.core import logger

# Third-party
import pytest

# Internal
from src.api.core import logger
from src.api.service.crud import question_crud
from src.api.service.question_manager import QuestionManager
from app_test.conftest import FakeQuestion


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def local_qm(dummy_storage):
    """Provide a QuestionManager instance backed by DummyStorage."""
    qm = QuestionManager(storage_service=dummy_storage, storage_type="local")
    logger.info("Initialized local question manager dummy %s", qm.base_path)
    return qm


@pytest.fixture
def fake_qpayload():
    """Minimal fake payload to construct a FakeQuestion."""
    return {
        "title": "Fake",
        "local_path": None,
        "blob_name": None,
        "id": uuid.UUID("6e81a590-935b-411a-9a7d-12ec4bfb5172"),
    }


@pytest.fixture
def create_question(local_qm, dummy_session, monkeypatch, fake_qpayload):
    """Provide a factory to create fake questions."""

    async def _create_question(override_payload=None):
        payload = override_payload or fake_qpayload
        fake_question = FakeQuestion(**payload)

        async def fake_create_question(question, session):
            return fake_question

        monkeypatch.setattr(question_crud, "create_question", fake_create_question)
        return await local_qm.create_question(
            question=fake_question, session=dummy_session
        )

    return _create_question


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


# Intialization
@pytest.mark.asyncio
async def test_initialization(local_qm, tmp_path):
    assert Path(local_qm.base_path) == (tmp_path / "questions")


# Creating questions
@pytest.mark.asyncio
async def test_create_question_check_payload(local_qm, create_question, fake_qpayload):
    # Given: a patched create_question returning a FakeQuestion
    q = await create_question()

    # Then: assertions
    assert isinstance(q, FakeQuestion)
    assert q.title == fake_qpayload["title"]
    assert q.id == fake_qpayload["id"]


@pytest.mark.asyncio
async def test_create_question_check_local_path(
    local_qm, create_question, fake_qpayload
):
    # Given: a patched create_question returning a FakeQuestion
    q = await create_question()

    # When: deriving the expected local path
    ## Should be a relative path like questions/title
    base_name = local_qm.base_name
    expected_path = (
        Path(base_name) / f"{fake_qpayload["title"]}_{fake_qpayload["id"]}"
    ).as_posix()
    assert q.local_path
    assert Path(q.local_path) == Path(expected_path)
