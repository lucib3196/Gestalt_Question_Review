import pytest
import pytest_asyncio
from src.api.models.file_model import File
from src.api.models.models import Question
from src.api.service import refactor_question_storage_service as qs
from src.api.response_models import FileData
from src.api.core.config import get_settings
from pathlib import Path

settings = get_settings()

@pytest.fixture
def set_testing_directory(tmp_path: Path):
    """
    Override QUESTIONS_PATH with a temporary directory during tests.
    """
    settings.QUESTIONS_PATH = tmp_path / "testing_path"

    yield tmp_path  # tests can use this if needed


@pytest.fixture
def sample_question(db_session, set_testing_directory) -> Question:
    """Question with no files."""
    q = Question(
        title="Sample Question",
        ai_generated=True,
        isAdaptive=False,
        createdBy="tester",
        user_id=1,
    )
    db_session.add(q)
    db_session.commit()
    db_session.refresh(q)
    return q


@pytest_asyncio.fixture
async def sample_question_with_file(db_session, set_testing_directory) -> Question:
    """Question with a single text file."""
    q = Question(
        title="Question with Files",
        ai_generated=True,
        isAdaptive=False,
        createdBy="user2",
        user_id=2,
    )
    db_session.add(q)
    db_session.commit()
    db_session.refresh(q)

    db_session.commit()

    file_content = "Hello World"
    f = FileData(filename="Test.txt", content=file_content)
    await qs.write_files_to_directory(q.id, files_data=[f], session=db_session)
    return q


@pytest_asyncio.fixture
async def sample_question_with_file_dict(db_session, set_testing_directory) -> Question:
    """Question with a single JSON-like file (dict or stringified JSON)."""
    q = Question(
        title="Question with Files",
        ai_generated=True,
        isAdaptive=False,
        createdBy="user2",
        user_id=2,
    )
    db_session.add(q)
    db_session.commit()
    db_session.refresh(q)

    file_content = {"a": "Data", "b": "Another data"}
    f = FileData(filename="Dummy.json", content=file_content)
    await qs.write_file_to_directory(q.id, file_data=f, session=db_session)

    return q
