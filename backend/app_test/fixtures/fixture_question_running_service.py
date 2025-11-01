import pytest
from pathlib import Path
from src.api.models.models import Question
from src.api.database import question
from app_test.conftest import test_config
from src.api.dependencies import QuestionManager
from src.api.response_models import FileData


@pytest.mark.asyncio
@pytest.fixture
async def create_question_with_code_file_serverjs(
    db_session, patch_questions_path, question_manager_test
):
    q_title = "Test_JavaScriptCode"
    filename = "server.js"
    q = Question(
        title=q_title,
        ai_generated=True,
        isAdaptive=False,
        createdBy="Luciano",
        user_id=1,
    )
    q_created = question.create_question(q, db_session)
    javascript_path = test_config.asset_path / "code_scripts" / "test.js"
    await question_manager_test.save_file_to_question(
        q_created.id,
        session=db_session,
        file=FileData(filename=filename, content=javascript_path.read_text()),
    )
    return q_created


@pytest.mark.asyncio
@pytest.fixture
async def create_question_with_code_file_serverpy(db_session, patch_questions_path):
    q_title = "Test_PythonCode"
    filename = "server.py"
    q = Question(
        title=q_title,
        ai_generated=True,
        isAdaptive=False,
        createdBy="Luciano",
        user_id=1,
    )
    q_created = question.create_question(
        q,
        db_session,
    )
    python_path = test_config.asset_path / "code_scripts" / "test.py"
    filedata = qs.FileData(filename=filename, content=python_path.read_text())
    await qs.write_files_to_directory(
        q_created.id, files_data=[filedata], session=db_session
    )
    return q_created


@pytest.fixture
def create_question_no_code(db_session, patch_questions_path):
    q_title = "Test_NoCode"
    q = Question(
        title=q_title,
        ai_generated=True,
        isAdaptive=False,
        createdBy="Luciano",
        user_id=1,
    )
    q_created = question.create_question(q, db_session)
    print("Created question succsefully")
    return q_created


@pytest.mark.asyncio
@pytest.fixture
async def create_question_empty_file_python(db_session, patch_questions_path):
    """
    Uses the new storage service instead of file_db. Note:
    the service rejects truly empty content, so we write a single newline.
    """
    q_title = "Test_PythonEmpty"
    filename = "server.py"
    q = Question(
        title=q_title,
        ai_generated=True,
        isAdaptive=False,
        createdBy="Luciano",
        user_id=1,
    )
    q_created = question.create_question(q, db_session)
    print("Created question succsefully")

    filedata = qs.FileData(filename=filename, content="\n")  # minimal non-empty content
    await qs.write_files_to_directory(
        q_created.id, files_data=[filedata], session=db_session
    )
    print(f"Added {q_title} and {filename} via storage service, returning question")
    return q_created


@pytest.mark.asyncio
@pytest.fixture
async def create_question_empty_file_js(db_session, patch_questions_path):
    """
    Uses the new storage service instead of file_db. Note:
    the service rejects truly empty content, so we write a single newline.
    """
    q_title = "Test_JavaScriptEmpty"
    filename = "server.js"
    q = Question(
        title=q_title,
        ai_generated=True,
        isAdaptive=False,
        createdBy="Luciano",
        user_id=1,
    )
    q_created = question.create_question(q, db_session)
    print("Created question succsefully")

    filedata = qs.FileData(filename=filename, content="\n")  # minimal non-empty content
    await qs.write_files_to_directory(
        q_created.id, files_data=[filedata], session=db_session
    )
    print(f"Added {q_title} and {filename} via storage service, returning question")
    return q_created
