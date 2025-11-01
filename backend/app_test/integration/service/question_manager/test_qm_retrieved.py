# --- Standard Library ---

# --- Third-Party ---
import pytest
import json

# --- Internal ---


@pytest.mark.asyncio
async def test_get_question(
    question_manager, db_session, question_payload_minimal_dict
):
    q1 = await question_manager.create_question(
        question_payload_minimal_dict, db_session
    )
    qretrieved = await question_manager.get_question(q1.id, db_session)
    assert qretrieved == q1


@pytest.mark.asyncio
async def test_get_question_identifier(
    question_manager, db_session, question_payload_minimal_dict
):
    q1 = await question_manager.create_question(
        question_payload_minimal_dict, db_session
    )
    identifier = await question_manager.get_question_identifier(q1.id, db_session)
    assert identifier == f"{q1.title}_{q1.id}"


@pytest.mark.asyncio
async def test_get_file(
    question_manager, db_session, question_payload_minimal_dict, file_data_payload
):
    q1 = await question_manager.create_question(
        question_payload_minimal_dict, db_session
    )
    await question_manager.save_files_to_question(q1.id, db_session, file_data_payload)

    for f in file_data_payload:
        content = await question_manager.read_file(q1.id, db_session, f.filename)
        assert content
        if isinstance(f.content, dict):
            assert f.content == json.loads(content)
        elif isinstance(f.content, (bytes, bytearray)):
            assert f.content == content


@pytest.mark.asyncio
async def test_get_all_files(
    question_manager, db_session, question_payload_minimal_dict, file_data_payload
):
    q1 = await question_manager.create_question(
        question_payload_minimal_dict, db_session
    )
    await question_manager.save_files_to_question(q1.id, db_session, file_data_payload)

    all_files = await question_manager.get_all_files(q1.id, db_session)
    assert set(all_files) == {f.filename for f in file_data_payload}
