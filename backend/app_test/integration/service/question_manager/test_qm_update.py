# --- Standard Library ---

# --- Third-Party ---
import pytest


# --- Internal ---
@pytest.mark.asyncio
async def test_update_question(
    question_manager, db_session, question_payload_minimal_dict
):
    q1 = await question_manager.create_question(
        question_payload_minimal_dict, db_session
    )
    await question_manager.update_question(q1.id, db_session, title="NewTitle")

    qretrieved = await question_manager.get_question(q1.id, db_session)
    assert qretrieved.title == "NewTitle"
