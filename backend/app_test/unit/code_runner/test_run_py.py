# --- Standard Library ---
from pathlib import Path
from typing import Literal

# --- Third-Party ---
import pytest

# --- Internal ---
from src.api.core import logger
from src.code_runner import run_js, run_py
from src.code_runner.models import CodeRunResponse
from src.utils import logs_contain


@pytest.fixture
def py_execution_result(py_script_path):
    """Fixture: runs the Python script and returns a validated response."""
    result = run_py.run_generate_py(path=str(py_script_path))
    response = CodeRunResponse.model_validate(result)
    assert response
    return response


def test_py_execution_success(py_execution_result):
    """Ensure the Python script executed successfully."""
    resp = py_execution_result
    assert resp.success is True
    assert resp.quiz_response is not None


def test_py_execution_returns_quiz_response(py_execution_result):
    """Verify the Python output includes a valid quiz response."""
    qr = py_execution_result.quiz_response
    assert qr.params == {"a": 1, "b": 2}
    assert qr.correct_answers["sum"] == 3


def test_py_execution_logs_expected_output(py_execution_result):
    """Ensure the Python logs contain expected messages and structures."""
    qr = py_execution_result.quiz_response
    assert logs_contain(qr.logs, "This is the value of a", "1")
    assert logs_contain(qr.logs, "This is the value of b", "2")

    # Structure log (Python repr)
    assert logs_contain(qr.logs, "This is a structure", "'params'")
    assert logs_contain(qr.logs, "This is a structure", "'a'", "1")
    assert logs_contain(qr.logs, "This is a structure", "'b'", "2")
