# --- Standard Library ---
from pathlib import Path
from typing import List, Optional, Union

# --- Third-Party ---
from fastapi import status
from starlette import status as starlette_status  # if you actually need both
import execjs
from typing import Any

# --- Internal ---
from src.code_runner.models import CodeRunResponse, CodeRunException


def normalize_path(path: Union[str, Path] | None) -> Path:
    if path is None:
        raise ValueError("No path provided")

    if isinstance(path, str):
        s = path.strip()
        if not s:
            raise ValueError("Empty path string")
        return Path(s)

    if isinstance(path, Path):
        return path

    raise TypeError(f"Unsupported path type: {type(path).__name__}")


def validate_filepath(path: str | Path, extensions: Optional[List[str]]) -> Path:
    """
    Validate a file path and ensure it exists, is a file, and has an allowed extension.

    Args:
        path (str | Path): The file path to validate.
        extensions (Optional[List[str]]): List of allowed file extensions (e.g. [".js", ".py"]).

    Returns:
        Path: The validated Path object.

    Raises:
        CodeRunException: If the file does not exist, is not a file, or has an unsupported extension.
    """
    try:
        path = normalize_path(path)

        if not path.exists() or not path.is_file():
            raise CodeRunException(
                error=f"File not found or filepath is not a file: {path}",
                http_status_code=status.HTTP_400_BAD_REQUEST,
            )

        if extensions and path.suffix not in set(extensions):
            raise CodeRunException(
                error=f"Unsupported file extension '{path.suffix}'. Expected one of {extensions}",
                http_status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            )

        return path

    except ValueError as e:
        raise CodeRunException(
            error=f"No file argument provided for JavaScript execution. {e}",
            http_status_code=status.HTTP_400_BAD_REQUEST,
        )


def append_javascript_logs(path: Path) -> str:
    try:
        user_js = path.read_text(encoding="utf-8")

        js_code = f"""
            var logs = [];

            // capture console.log into logs array
            console.log = function(...args) {{
                const processed = args.map(arg => {{
                    if (typeof arg === "object") {{
                        try {{
                            return JSON.stringify(arg);
                        }} catch (e) {{
                            return "[Unserializable Object]";
                        }}
                    }}
                    return String(arg);
                }});

                logs.push(processed.join(" "));
            }};

            // `generate` should exist in user code.
            // We allow an optional arg; tests can pass a fixed value.
            {user_js}
            function callWithLogs(arg) {{
                let result = null;
                let params = {{}};             // default
                let correct_answers = [];      // default

                try {{
                    const safeArg = (arg && typeof arg === "object") ? arg : {{}};
                    params = safeArg;

                    if (typeof generate === "function") {{
                        const out = generate(safeArg);

                        if (out && typeof out === "object") {{
                            result = out;
                            if ("correct_answers" in out) {{
                                correct_answers = out.correct_answers;
                            }}
                        }} else {{
                            logs.push("generate returned non-object output");
                            result = out;
                        }}
                    }} else {{
                        logs.push("generate is not a function");
                    }}
                }} catch (e) {{
                    const msg = (e && e.message) ? e.message : String(e);
                    logs.push(`Error in generate: ${{msg}}`);
                    if (e && e.stack) {{
                        logs.push(`Stack: ${{e.stack}}`);
                    }}
                }}

                return {{
                    result,
                    logs,
                    params,
                    correct_answers
                }};
            }}
        """

        return js_code

    except UnicodeDecodeError:
        raise CodeRunException(
            error="File is not valid UTF-8 text.",
            http_status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )

    except OSError as e:
        raise CodeRunException(
            error=f"Failed to read file: {e}",
            http_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def compile_js_code(js_code: str):
    try:
        return execjs.compile(js_code)
    except execjs.RuntimeUnavailableError:
        raise CodeRunException(
            error="No JavaScript runtime available. Install Node.js so execjs can use it.",
            http_status_code=status.HTTP_424_FAILED_DEPENDENCY,
        )
    except execjs.ProgramError as e:
        raise CodeRunException(
            error=f"JavaScript compile error: {e}",
            http_status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    except Exception as e:
        raise CodeRunException(
            error=f"Unexpected error compiling JavaScript: {e}",
            http_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def validate_generate_function_js(ctx) -> bool:
    try:
        has_generate = ctx.eval("typeof generate === 'function'")
        if not has_generate:
            raise CodeRunException(
                error="The JavaScript file does not define a function named `generate`.",
                http_status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return True
    except execjs.ProgramError as e:
        raise CodeRunException(
            error=f"Error checking for `generate` function: {e}",
            http_status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


def run_javascript(ctx, isTesting: bool):
    try:
        # Execute: tests pass a fixed arg (e.g., 2); normal run passes null
        raw = ctx.call("callWithLogs", 2 if isTesting else None)
        if not isinstance(raw, dict):
            raise CodeRunException(
                error="JavaScript did not return an object. Expected { result, logs }.",
                http_status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return raw
    except execjs.ProgramError as e:
        raise CodeRunException(
            error=f"JavaScript runtime error: {e}",
            http_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    except Exception as e:
        raise CodeRunException(
            error=f"Unexpected error during JS execution: {e}",
            http_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def validate_test_result_structure(testing_data: dict[str, Any]):
    if testing_data is None:
        raise CodeRunException(
            error="Expected testing results received none",
            http_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    else:
        if not isinstance(testing_data, dict):
            raise CodeRunException(
                error="Test run expected `result.test_results` as a dict.",
                http_status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        # Check ifpass is present
        passed = testing_data.get("pass")
        if passed not in (0, 1, True, False):
            raise CodeRunException(
                error="`test_results.pass` must be 0/1 or boolean.",
                http_status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        if not bool(passed):
            msg = testing_data.get("message", "JavaScript test failed.")
            raise CodeRunException(
                error=f"Test failed: {msg}",
                http_status_code=status.HTTP_200_OK,
            )
