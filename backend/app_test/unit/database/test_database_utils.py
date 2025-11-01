import pytest
from uuid import UUID, uuid4
from src.utils.database_utils import *
from src.api.models.models import Topic, Language, QType, Question


def test_convert_uuid_passes_uuid():
    random_uuid = uuid4()
    assert convert_uuid(random_uuid) == random_uuid


def test_conver_valid_uuid():
    s = "12345678-1234-5678-1234-567812345678"
    result = convert_uuid(s)
    assert isinstance(result, UUID)
    assert str(result) == s


@pytest.mark.parametrize(
    "bad_input",
    [
        "not-a-uuid",
        "1234",
        1234,  # non-string, non-UUID
        None,  # None should fail
        {"id": "1234"},  # wrong type
    ],
)
def test_bad_uuid_input(bad_input):
    with pytest.raises(ValueError) as exec:
        convert_uuid(bad_input)
    assert "Could not convert" in str(exec.value)


@pytest.mark.parametrize(
    "payload",
    [
        {"target_cls": Topic, "value": "Not a Topic", "lookup_field": "name"},
        {"target_cls": Language, "value": "Not a Language", "lookup_field": "name"},
        {"target_cls": QType, "value": "Not a Qtype", "lookup_field": "name"},
    ],
)
def test_resolve_or_create_creating_new_value(db_session, payload):
    # Act
    created_model, existed = resolve_or_create(
        db_session,
        target_cls=payload["target_cls"],
        value=payload["value"],
        lookup_field=payload["lookup_field"],
    )

    # Assert
    assert created_model is not None
    assert existed is False
    assert created_model.id is not None
    assert created_model.name.lower().strip() == payload["value"].lower().strip()


@pytest.mark.parametrize(
    "rel_attributes",
    [
        {"target_model": Question, "target_rel": "topics"},
        {"target_model": Question, "target_rel": "languages"},
        {"target_model": Question, "target_rel": "qtypes"},
    ],
)
def test_is_relationship(rel_attributes):
    assert is_relationship(
        model=rel_attributes["target_model"], attr_name=rel_attributes["target_rel"]
    )


@pytest.mark.parametrize(
    "rel",
    [{"target_model": Question, "target_rel": "topics"}],
)
def test_get_model_relationship_data(rel):
    # Act: request all relationships for the model
    result = view_models_relationship(model=rel["target_model"])

    # Basic shape
    assert isinstance(result, dict)
    assert rel["target_rel"] in result

    # Inspect the 'topics' relationship
    prop = result[rel["target_rel"]]
    assert prop.key == "topics"
    assert prop.uselist is True  # many-to-many -> list
    # Target mapper should be Topic
    assert prop.mapper.class_ is Topic
    # Back-populates should point back to the Question-side attribute
    assert getattr(prop, "back_populates", None) == "questions"
