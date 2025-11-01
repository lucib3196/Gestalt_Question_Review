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
def js_execution_result(js_script_path):
    """Fixture: runs the JavaScript file and returns a validated response."""
    result = run_js.execute_javascript(path=js_script_path)
    response = CodeRunResponse.model_validate(result)
    assert response
    return response


def test_js_execution_success(js_execution_result):
    """Ensure the JavaScript executed successfully."""
    resp = js_execution_result
    assert resp.success is True


def test_js_execution_returns_quiz_response(js_execution_result):
    """Verify the JavaScript output includes a valid quiz response."""
    qr = js_execution_result.quiz_response
    assert qr is not None
    assert qr.params == {"a": 1, "b": 2}
    assert qr.correct_answers["sum"] == 3


def test_js_execution_logs_expected_output(js_execution_result):
    """Ensure the JavaScript logs contain expected messages and data."""
    qr = js_execution_result.quiz_response
    assert logs_contain(qr.logs, "This is the value of a", "1")
    assert logs_contain(qr.logs, "This is the value of b", "2")
    assert logs_contain(qr.logs, "Here is a structure")
    assert logs_contain(qr.logs, "Here is a structure") and (
        logs_contain(qr.logs, "Here is a structure", '"a"', "1")  # JSON-like
        or logs_contain(qr.logs, "Here is a structure", "a", "1")  # fallback
    )
