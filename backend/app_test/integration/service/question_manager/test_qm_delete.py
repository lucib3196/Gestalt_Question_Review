# --- Standard Library ---

# --- Third-Party ---
import pytest

# --- Internal ---
@pytest.mark.asyncio
async def test_delete_file(question_manager, db_session, question_payload_minimal_dict, file_data_payload):
    q1 = await question_manager.create_question(question_payload_minimal_dict, db_session)
    await question_manager.save_files_to_question(q1.id, db_session, file_data_payload)

    for f in file_data_payload:
        await question_manager.delete_question_file(q1.id, db_session, f.filename)
        assert await question_manager.read_file(q1.id, db_session, f.filename) is None


@pytest.mark.asyncio
async def test_delete_question(question_manager, db_session, question_payload_minimal_dict, file_data_payload):
    q1 = await question_manager.create_question(question_payload_minimal_dict, db_session)
    await question_manager.save_files_to_question(q1.id, db_session, file_data_payload)

    await question_manager.delete_question(q1.id, db_session)
    assert await question_manager.get_question(q1.id, db_session) is None
