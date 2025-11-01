# --- Standard Library ---

# --- Third-Party Libraries ---
import pytest

# --- Internal Imports ---
from src.utils.test_utils import prepare_file_uploads
from app_test.integration.web.conftest import create_question
from src.code_runner.models import QuizData

# -----------------------------------------
# Tests
# -----------------------------------------


def run_server(client, qid, language):
    resp = client.post(f"/question_running/run_server/{qid}/{language}")
    assert resp.status_code == 200, resp.text
    response_data = resp.json()
    quiz_data = QuizData.model_validate(response_data)



@pytest.mark.parametrize("language", ["python", "javascript"])
def test_question_server_run(
    language, test_client, server_files, question_data, db_session
):
    q_created = create_question(
        test_client,
        question_data,
        metadata=None,
        files=prepare_file_uploads(server_files),
    )
    run_server(test_client, q_created.id, language=language)
    
