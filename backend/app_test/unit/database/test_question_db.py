from src.api.database import question as qdb
import pytest
from src.utils import pick
from src.api.models.models import Topic, Language, Question, QType
from src.api.core.logging import logger








# ----------------------
# Minimal creation (no topics)
# ----------------------
def test_create_question(db_session, question_payload):
    qcreated = qdb.create_question(question_payload, db_session)
    assert qcreated
    for key, _ in question_payload.model_dump().items():
        assert getattr(qcreated, key) == getattr(question_payload, key)


def test_create_question_with_relationship_data(
    db_session, question_payload, relationship_payload
):
    qcreated = qdb.create_question(question_payload, db_session, relationship_payload)
    assert qcreated
    for key, _ in question_payload.model_dump().items():
        assert getattr(qcreated, key) == getattr(question_payload, key)

    for key, _ in relationship_payload.items():
        logger.info("Relationship data %s", getattr(qcreated, key))
        qrel = getattr(qcreated, key)
        # Convert to a list with just the names and set for comparing
        assert set([r.name for r in qrel]) == set(relationship_payload[key])


def test_get_question(db_session, question_payload):
    qcreated = qdb.create_question(question_payload, db_session)
    assert qcreated == qdb.get_question(qcreated.id, db_session)


def test_get_all_questions(db_session, combined_payload):
    # Create data
    for q in combined_payload:
        qcreated = qdb.create_question(q, db_session)
        assert qcreated
    questions = qdb.get_all_questions(db_session)
    assert isinstance(questions, list)
    assert all(isinstance(q, Question) for q in questions)
    assert len(combined_payload) == len(questions)


# Test Deleting questions
def test_delete_all_questions(db_session, combined_payload):
    for q in combined_payload:
        qcreated = qdb.create_question(q, db_session)
        assert qcreated
    qdb.delete_all_questions(db_session)
    questions = qdb.get_all_questions(db_session)
    assert isinstance(questions, list)
    assert questions == []


def test_delete_single(db_session, combined_payload):
    for q in combined_payload:
        qcreated = qdb.create_question(q, db_session)
        assert qcreated

        # Get the question
        assert qdb.get_question(qcreated.id, db_session)
        qdb.delete_question(qcreated.id, db_session)
        assert qdb.get_question(qcreated.id, db_session) is None
