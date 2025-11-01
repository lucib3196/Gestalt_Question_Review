from src.api.models.models import Question
from src.api.database import generic_db as gdb


def test_get_all_model_relationships():
    question_relationships = ["topics", "languages", "qtypes", "created_by"]
    all_relationships = gdb.get_all_model_relationships(Question)
    assert set(all_relationships.keys()) == set(question_relationships)


def test_get_model_relationship_data(
    create_question_with_relationship, relationship_payload
):
    q = create_question_with_relationship
    for rel_name, data in relationship_payload.items():
        data = getattr(q, rel_name)
        assert [d.name in relationship_payload[rel_name] for d in data]


def test_is_relationship():
    assert gdb.is_relationship(Question, "RandomRel") is False
    assert gdb.is_relationship(Question, "topics")


def test_get_all_model_relationship_data(
    create_question_with_relationship, relationship_payload
):
    q = create_question_with_relationship
    rel_data = gdb.get_all_model_relationship_data(q, Question)
    assert rel_data
    for rel_name, data in rel_data.items():
        # There may be relationships that the payload does not have so skip these
        if rel_name not in relationship_payload:
            continue
        assert set(relationship_payload[rel_name]) == set([d.name for d in data])
