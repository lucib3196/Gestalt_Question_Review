import pytest
from pathlib import Path

# --- Internal Imports ---
from src.code_runner.runtime_switcher import run_generate
from src.code_runner.models import CodeRunResponse, CodeRunException


# --- Fixtures ---
@pytest.fixture(params=["js_script_path", "py_script_path"])
def script_path(request):
    """Fixture: dynamically selects between JS and Python script fixtures."""
    language = "javascript" if request.param == "js_script_path" else "python"
    path = request.getfixturevalue(request.param)
    return path, language


@pytest.fixture(params=["js_script_path", "py_script_path"])
def script_path_wrong(request):
    """Fixture: intentionally mismatched language and file combination."""
    language = "python" if request.param == "js_script_path" else "javascript"
    path = request.getfixturevalue(request.param)
    return path, language


@pytest.fixture
def executed_response(script_path):
    """Fixture: executes the runtime switcher for the given language."""
    path, language = script_path
    resp = run_generate(path, language)
    response = CodeRunResponse.model_validate(resp)
    assert response
    return response


# --- Tests ---
def test_execution_success(executed_response):
    """Ensure valid script executes successfully."""
    resp = executed_response
    assert resp.success is True
    assert resp.quiz_response


def test_execution_fails_with_wrong_runtime(script_path_wrong):
    """Ensure mismatched runtime fails as expected."""
    path, language = script_path_wrong
    with pytest.raises(CodeRunException) as excinfo:
        resp = run_generate(path, language)
