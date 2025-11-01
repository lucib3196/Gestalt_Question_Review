# Configuration file for tests – these are global and generic

# --- Standard Library ---
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID

# Testing logs
from src.api.core.logging import in_test_ctx

# --- Third-Party ---
import pytest
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

# --- Internal ---
from src.api.core import logger
from src.api.core.config import get_settings
from src.api.service.storage import StorageService
from src.api.response_models import FileData
from src.api.service.storage.local_storage import LocalStorageService
from src.api.service.question_manager import QuestionManager
from src.firebase.storage import FirebaseStorage
from src.firebase.core import initialize_firebase_app

settings = get_settings()
initialize_firebase_app()


@asynccontextmanager
async def on_startup_test(app: FastAPI):
    # skip init_db in tests
    yield


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


class DummyStorage(StorageService):
    """A fake storage service used for testing."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.basename = self.path.name

    def get_base_path(self) -> str | Path:
        return self.path

    def get_base_name(self) -> str:
        return self.path.name

    def get_relative_storage_path(self, identifier: str) -> str | Path:
        return self.get_storage_path(identifier).relative_to(self.path.parent)

    def get_storage_path(self, identifier: str) -> Path:
        return self.path / identifier

    def does_storage_path_exist(self, identifier: str) -> bool:
        return self.path.exists()

    def create_storage_path(self, identifier: str) -> Path:
        Path.mkdir(self.get_storage_path(identifier), parents=True, exist_ok=True)
        return self.get_storage_path(identifier)

    def get_filepath(self, identifier: str, filename: str) -> Path:
        return self.get_storage_path(identifier) / filename


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
def dummy_storage(tmp_path):
    path = Path(tmp_path) / "questions"
    logger.debug("Initialized dummy storage with path %s ", path)
    return DummyStorage(path)


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
def qpayload_bad():
    return {"Data": "Some Content"}


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


# Storage Fixtures
@pytest.fixture(scope="function")
def cloud_storage_service():
    """
    Provides a FireCloudStorageService connected to the configured test bucket.
    """

    base_path = "integration_test"
    settings.STORAGE_BUCKET

    return FirebaseStorage(settings.STORAGE_BUCKET, base_path)


@pytest.fixture(autouse=True)
def clean_up_cloud(cloud_storage_service):
    # Setup code (before test runs)
    yield
    # Teardown code (after test finishes)
    cloud_storage_service.hard_delete()
    logger.debug("Deleting Bucket Cleaning Up")


@pytest.fixture
def local_storage(tmp_path):
    """Provide a LocalStorageService rooted in a temp directory."""
    base = tmp_path / "questions"
    return LocalStorageService(base)


@pytest.fixture
def question_manager_local(local_storage):
    """Provide a QuestionManager using LocalStorageService."""
    return QuestionManager(local_storage, "local")


@pytest.fixture
def question_manager_cloud(cloud_storage_service):
    return QuestionManager(cloud_storage_service, "cloud")


@pytest.fixture(scope="function", params=["local", "cloud"])
def question_manager(request, question_manager_local, question_manager_cloud):
    storage_type = request.param
    if storage_type == "cloud":
        qm = question_manager_cloud
    elif storage_type == "local":
        qm = question_manager_local
    else:
        raise ValueError("Incorrect storage type")
    return qm
