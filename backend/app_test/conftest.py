from contextlib import asynccontextmanager
from types import SimpleNamespace
from typing import List
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel
from sqlmodel import Session, create_engine

from src.api.core import logger, in_test_ctx
from src.api.core.config import get_settings
from src.api.database.database import Base, get_session
from src.api.main import get_application
from src.api.models import FileData
from src.api.service.question.question_manager import QuestionManager, get_question_manager
from src.api.service.storage_manager import (
    get_storage_manager,
)
from src.firebase.core import initialize_firebase_app
from src.storage.firebase_storage import FirebaseStorage
from src.storage.local_storage import LocalStorageService


settings = get_settings()
initialize_firebase_app()


@asynccontextmanager
async def on_startup_test(app: FastAPI):
    """Async startup context for tests (skips DB initialization)."""
    yield


# -----------------------------
# Database Fixtures
# -----------------------------
@pytest.fixture(scope="function")
def test_engine(tmp_path):
    """Provide a temporary SQLite engine for testing."""
    url = f"sqlite:///{tmp_path}/test.db"
    engine = create_engine(
        url,
        echo=False,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine):
    """Provide a new SQLModel session for each test with isolation."""
    with Session(test_engine, expire_on_commit=False) as session:
        yield session
        session.rollback()


@pytest.fixture(autouse=True)
def _clean_db(db_session, test_engine):
    """Automatically reset database tables between tests."""
    logger.debug("Cleaning Database")
    Base.metadata.drop_all(test_engine)
    Base.metadata.create_all(test_engine)


# -----------------------------
# Question Manager Fixture
# -----------------------------
@pytest.fixture(scope="function")
def question_manager(db_session):
    """Provide a QuestionManager instance for database operations."""
    return QuestionManager(db_session)


# -----------------------------
# Storage Fixtures
# -----------------------------
@pytest.fixture(scope="function")
def cloud_storage_service():
    """Provide a FirebaseStorage instance connected to the test bucket."""
    base_path = "integration_test"
    return FirebaseStorage(settings.STORAGE_BUCKET, base_path)


@pytest.fixture(autouse=True)
def clean_up_cloud(cloud_storage_service):
    """Clean up the test bucket after each test."""
    yield
    cloud_storage_service.hard_delete()
    logger.debug("Deleting Bucket - Cleaning Up")


@pytest.fixture(scope="function")
def local_storage(tmp_path):
    """Provide a LocalStorageService rooted in a temporary directory."""
    root = tmp_path 
    return LocalStorageService(root, base="questions")


# =========================================
# API Fixtures
# =========================================
@pytest.fixture(scope="session")
def test_app():
    """Create the FastAPI app once for all tests."""
    app = get_application()
    app.router.lifespan_context = on_startup_test
    return app


@pytest.fixture(scope="function", params=["local", "cloud"])
def storage_mode(request):
    """Single shared parameter controlling local/cloud mode."""
    return request.param


@pytest.fixture(scope="function")
def get_storage_service(storage_mode, cloud_storage_service, local_storage):
    """Select either cloud or local storage for parameterized tests."""
    if storage_mode == "cloud":
        return cloud_storage_service
    elif storage_mode == "local":
        return local_storage
    raise ValueError(f"Invalid storage type: {storage_mode}")


# @pytest.fixture(scope="function")
# def patch_app_settings(storage_mode, monkeypatch):
#     """
#     Patch STORAGE_SERVICE env var for this test's storage mode.
#     Ensures get_settings() reflects the correct value.
#     """
#     monkeypatch.setenv("STORAGE_SERVICE", storage_mode)

#     # Force settings reload (avoid cached instance if you use lru_cache)
#     from src.api.core import config

#     if hasattr(config.get_settings, "cache_clear"):
#         config.get_settings.cache_clear()  # ensure settings re-read from env

#     settings = config.get_settings()
#     assert (
#         settings.STORAGE_SERVICE == storage_mode
#     ), f"Settings patch failed. Expected {storage_mode}, got {settings.STORAGE_SERVICE}"
#     return settings


@pytest.fixture(scope="function")
def test_client(db_session, get_storage_service, storage_mode,):
    """
    Provide a configured FastAPI TestClient with overridden dependencies
    for both local and cloud storage modes.
    """
    app = get_application()
    app.router.lifespan_context = on_startup_test
    # patch_app_settings # type: ignore

    def override_get_db():
        yield db_session

    async def override_qm():
        yield QuestionManager(db_session)

    async def override_storage():
        yield get_storage_service

    app.dependency_overrides[get_session] = override_get_db
    app.dependency_overrides[get_question_manager] = override_qm
    app.dependency_overrides[get_storage_manager] = override_storage

    with TestClient(app, raise_server_exceptions=True) as client:
        yield client


class FakeQuestion(BaseModel):
    """A fake Question model for testing."""

    title: str | None
    local_path: str | None
    blob_name: str | None = None
    id: UUID


class DummySession:
    """A fake DB session used for testing."""

    def __init__(self):
        self.committed = False
        self.refreshed = False

    def commit(self):
        self.committed = True

    def refresh(self, obj):
        self.refreshed = True

    def add(self, obj):
        pass


def make_qc_stub(question: FakeQuestion, session: DummySession):
    """Return a qc stub with async get_question_by_id and safe_refresh_question."""

    async def _get_question_by_id(qid, _session):
        return question

    async def _safe_refresh_question(qid, _session):
        _session.commit()
        _session.refresh(question)
        return question

    return SimpleNamespace(
        get_question_by_id=_get_question_by_id,
        safe_refresh_question=_safe_refresh_question,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def dummy_session():
    return DummySession()


@pytest.fixture
def patch_question_dir(monkeypatch):
    """Patch QUESTIONS_DIRNAME to a test directory name."""
    dir_name = "test_question"
    monkeypatch.setattr(settings, "QUESTIONS_DIRNAME", dir_name)
    return dir_name


@pytest.fixture
def patch_questions_path(monkeypatch, tmp_path, patch_question_dir):
    """Patch BASE_PATH and QUESTIONS_PATH to a temporary directory on disk."""
    base_path = tmp_path.resolve()
    monkeypatch.setattr(settings, "BASE_PATH", str(base_path))

    questions_path = base_path / patch_question_dir
    questions_path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(settings, "QUESTIONS_PATH", str(questions_path))

    return questions_path


@pytest.fixture(autouse=True)
def mark_logs_in_test():
    """Mark logs as being inside test context for duration of each test."""
    token = in_test_ctx.set(True)
    yield
    in_test_ctx.reset(token)


from app_test.fixtures.fixture_crud import *


@pytest.fixture
def file_data_payload() -> List[FileData]:
    """Provide a list of FileData objects with string, dict, and binary content."""
    text_content = "Hello World"
    dict_content = {"key": "value", "number": 123}
    binary_content = b"\x00\x01\x02\x03"

    return [
        FileData(filename="Test.txt", content=text_content),
        FileData(filename="Config.json", content=dict_content),
        FileData(filename="Binary.bin", content=binary_content),
    ]


@pytest.fixture
def question_file_payload() -> List[FileData]:
    files_data = [
        ("question.html", "Some question text"),
        ("solution.html", "Some solution"),
        ("server.js", "some code content"),
        ("meta.json", {"content": "some content"}),
    ]
    return [FileData(filename=f[0], content=f[1]) for f in files_data]


@pytest.fixture
def question_additional_metadata():
    return {
        "topics": ["Mechanics", "Statics"],
        "languages": ["python", "javascript"],
        "qtype": ["numeric"],
    }
