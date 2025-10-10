# --- Standard Library ---
import subprocess
from pathlib import Path
from typing import Any, Dict, Union

# --- Third-Party ---
import json5
from pydantic import ValidationError
from starlette import status

# --- Internal ---
from src.api.core import logger
from src.code_runner.models import CodeRunResponse, QuizData, CodeRunException
from src.code_runner.utils import *
from .utils import *


def run_js(path: str) -> CodeRunResponse:
    """
    Runs a JavaScript file using Node.js and parses its output as JSON.
    Expects the JS file to output a JSON object via console.log(generate()).
    """
    js_path = str(Path(path))  # Ensure cross-platform path handling

    try:
        result = subprocess.run(
            ["node", js_path, "generate()"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except subprocess.TimeoutExpired:
        return CodeRunResponse(
            success=False,
            error="JavaScript execution timed out.",
            quiz_response=None,
            http_status_code=504,
        )
    except Exception as e:
        return CodeRunResponse(
            success=False,
            error=f"Failed to execute JavaScript file '{js_path}': {e}",
            quiz_response=None,
            http_status_code=500,
        )

    stdout = result.stdout.strip()
    stderr = result.stderr.strip()

    if result.returncode != 0:
        return CodeRunResponse(
            success=False,
            error=f"JavaScript script returned an error:\n{stderr or stdout}",
            quiz_response=None,
            http_status_code=500,
        )

    if not stdout:
        return CodeRunResponse(
            success=False,
            error="No output was returned from the JavaScript script. Hint: There must be a console.log(generate())",
            quiz_response=None,
            http_status_code=500,
        )

    try:
        parsed = json5.loads(stdout)

    except Exception as e:
        return CodeRunResponse(
            success=False,
            error=f"Failed to parse output as JSON: {e}\nOutput was:\n{stdout}",
            quiz_response=None,
            http_status_code=400,
        )

    if not isinstance(parsed, dict):
        return CodeRunResponse(
            success=False,
            error="Output is not a JSON object (dict).",
            quiz_response=None,
            http_status_code=400,
        )

    try:
        quiz_data = QuizData(**parsed)
    except ValidationError as ve:
        return CodeRunResponse(
            success=False,
            error=f"Output JSON did not match expected schema: {ve}",
            quiz_response=None,
            http_status_code=422,
        )

    return CodeRunResponse(
        success=True,
        error=None,
        http_status_code=200,
        quiz_response=quiz_data,
    )


def execute_javascript(
    path: Union[str, Path], isTesting: bool = False
) -> CodeRunResponse:
    """
    Execute a JavaScript file, validate its structure, and return a CodeRunResponse.

    Args:
        path (Union[str, Path]): Path to the JavaScript file (.js or .mjs).
        isTesting (bool): Whether the execution is in test mode.

    Returns:
        CodeRunResponse: Success response containing validated QuizData.

    Raises:
        CodeRunException: For validation, runtime, or schema errors.
    """
    try:
        # Validate input file path
        file_path = validate_filepath(path, extensions=[".mjs", ".js"])

        # Read and wrap JS with logging + shim
        js_code = append_javascript_logs(file_path)

        # Compile JS
        ctx = compile_js_code(js_code)

        # Ensure `generate` function exists
        validate_generate_function_js(ctx)

        # Run JS and extract results
        raw = run_javascript(ctx, isTesting)
        logger.info("Ran JavaScript successfully")

        js_result: Any = raw.get("result")
        logs: list[str] = raw.get("logs", [])

        # Ensure result exists
        if js_result is None:
            raise CodeRunException(
                error=(
                    "Missing `result` in JavaScript return object. "
                    "Nothing was returned from the JavaScript code."
                ),
                http_status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        logger.debug("Raw JavaScript Results: %s", js_result)
        logger.debug("Captured logs: %s", logs)

        # Ensure result type
        if not isinstance(js_result, dict):
            raise CodeRunException(
                error=(
                    f"Expected JavaScript result to be of type dict, "
                    f"but received {type(js_result).__name__}"
                ),
                http_status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        # Construct payload
        payload: Dict[str, Any] = {**js_result, "logs": logs}

        # Validate test metadata if in test mode
        if isTesting:
            test_meta: Dict[str, Any] = js_result.get("test_results", {})
            validate_test_result_structure(test_meta)

        # Validate against QuizData schema
        quiz_data = QuizData(**payload)

        return CodeRunResponse(
            success=True,
            error=None,
            quiz_response=quiz_data,
            http_status_code=status.HTTP_200_OK,
        )

    except CodeRunException:
        raise

    except ValidationError as e:
        raise CodeRunException(
            error=f"Result did not match QuizData schema: {e}",
            http_status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    except Exception as e:
        raise CodeRunException(
            error=f"Unexpected error during JavaScript execution: {e}",
            http_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def test():
    path = Path(r"code_runner\test2.js")

    print(execute_javascript(path, True))


if __name__ == "__main__":
    test()
