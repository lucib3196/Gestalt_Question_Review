# This conftest file sets up the FastAPI application and dependencies
# used for integration testing.

# ==============================
# Standard Library
# ==============================
import json
from contextlib import asynccontextmanager
from pathlib import Path

# ==============================
# Third-Party Libraries
# ==============================
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.api.response_models import QuestionReadResponse

# ==============================
# Local Application Imports
# ==============================
from src.api.main import get_application
from src.api.database.database import get_session
from src.api.dependencies import get_question_manager
from src.api.response_models import FileData


@asynccontextmanager
async def on_startup_test(app: FastAPI):
    # skip init_db in tests
    yield


# -----------------------------------------
# Application fixture
# -----------------------------------------
@pytest.fixture(scope="session")
def test_app():
    """Create the FastAPI app once for all tests."""
    app = get_application()
    app.router.lifespan_context = on_startup_test
    return app


# -----------------------------------------
# Test client fixture (parametrized for local/cloud)
# -----------------------------------------
@pytest.fixture(scope="function", params=["local", "cloud"])
def test_client(db_session, request, question_manager_cloud, question_manager_local):
    app = get_application()

    storage_type = request.param
    if storage_type == "cloud":
        qm = question_manager_cloud
    elif storage_type == "local":
        qm = question_manager_local
    else:
        raise ValueError("Incorrect storage type")

    app.router.lifespan_context = on_startup_test

    def override_get_db():
        yield db_session

    async def override_get_qm():
        yield qm

    app.dependency_overrides[get_session] = override_get_db
    app.dependency_overrides[get_question_manager] = override_get_qm

    with TestClient(app) as client:
        yield client


# -----------------------------------------
# Supporting data fixtures
# -----------------------------------------
@pytest.fixture
def question_data():
    """Minimal question payload."""
    return {
        "title": "SomeTitle",
        "ai_generated": True,
        "isAdaptive": True,
        "createdBy": "John Doe",
        "user_id": 1,
    }


def create_question(client, payload, metadata=None, files=None):
    data = {"question": json.dumps(payload)}
    if metadata:
        data["additional_metadata"] = json.dumps(metadata)

    resp = client.post("/questions/", data=data, files=files)
    assert resp.status_code == 201, resp.text

    # Re-validate response data against the schema
    response_data = resp.json()
    validated = QuestionReadResponse.model_validate(response_data)
    assert validated

    return validated.question


def retrieve_question(client, qid):
    resp = client.get(f"/questions/{qid}")
    assert resp.status_code == 200, resp.text
    response_data = resp.json()
    validated = QuestionReadResponse.model_validate(response_data)
    assert validated
    return validated.question


@pytest.fixture
def server_files():
    """Static assets used by question endpoints."""
    base = Path("src/app_test/test_assets/code")
    return [
        FileData(filename="server.js", content=(base / "generate.js").read_bytes()),
        FileData(filename="server.py", content=(base / "generate.py").read_bytes()),
    ]
