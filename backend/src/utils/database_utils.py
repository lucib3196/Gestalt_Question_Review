# Stdlib
from typing import Dict, List, Optional, Tuple, Type, TypeVar, Union
from uuid import UUID

# Third-party
from sqlalchemy import String, cast, func
from sqlalchemy.inspection import inspect
from sqlalchemy.orm.exc import UnmappedInstanceError
from sqlalchemy.orm.properties import RelationshipProperty
from sqlmodel import SQLModel, select

# Local
from src.api.database import SessionDep
from datetime import datetime


def convert_uuid(uuid: str | UUID) -> UUID:
    try:
        if isinstance(uuid, UUID):
            return uuid
        else:
            return UUID(uuid)
    except Exception as e:
        raise ValueError(f"Could not convert {type(uuid)} into UUID")


T = TypeVar("T", bound=SQLModel)





def view_models_relationship(
    model: Type[SQLModel], relationships: Optional[List[Union[str, type]]] = None
):
    mapper = inspect(model)
    all_rels = {rel.key: rel for rel in mapper.relationships}

    if relationships is None:
        return all_rels

    resolved: Dict[str, RelationshipProperty] = {}

    for item in relationships:
        # Case 1: explicit relationship name as string
        if isinstance(item, str):
            name = item
            if name not in all_rels:
                raise ValueError(
                    f"Model {model.__name__} has no relationship named '{name}'."
                )
            resolved[name] = all_rels[name]
            continue
        # Case 2: A target class was provided
        if isinstance(item, type):
            target_cls = item
            matches = [
                rel for rel in all_rels.values() if rel.mapper.class_ is target_cls
            ]
            if not matches:
                raise ValueError(
                    f"Model {model.__name__} has no relationship targeting class {target_cls.__name__}."
                )
            rel = matches[0]
            resolved[rel.key] = rel
            continue
        raise ValueError(f"Unsupported relationship spec: {item!r}")

    return resolved


# TODO No Test Currently [Note]:
# Note This kinda got tested with question_db but no individual test
def get_models_relationship_data(model: SQLModel, relationship: str):
    # Check that it is a valid model
    try:
        r = view_models_relationship(type(model), [relationship])
        assert r[relationship]
    except Exception as e:
        raise ValueError(
            f"Relationship {relationship} is not valid for model of type {type(model)} error {str(e)}"
        )
    try:
        return getattr(model, relationship)
    except Exception as e:
        raise e


def pick_related_label_col(target_cls):
    """
    Try to pick a 'label' column on the related class for string lookups.
    Preference: .name -> .title -> first String column -> primary key.
    """
    if hasattr(target_cls, "name"):
        return getattr(target_cls, "name")
    if hasattr(target_cls, "title"):
        return getattr(target_cls, "title")


def string_condition(col, raw_val: str, partial: bool = True):
    """
    Case-insensitive string filter. If partial=True, uses ILIKE %v%,
    else equality on lower().
    """
    if partial:
        return func.lower(cast(col, String)).like(f"%{raw_val.lower()}%")
    return func.lower(cast(col, String)) == raw_val.lower()


def normalize_kwargs(kwargs: dict):
    normalized = {}
    for key, value in kwargs.items():
        if isinstance(value, list):
            for v in value:
                if isinstance(v, dict):
                    f = [v.get("name")]
                else:
                    f = [v]

                normalized[key] = f

        else:
            normalized[key] = value
    return normalized


def safe_python_type(col):
    try:
        return col.type.python_type
    except (NotImplementedError, AttributeError):
        return object


def normalize_timestamps(data: dict) -> dict:
    for field in ("created_at", "updated_at", "deleted_at", "storage_updated_at"):
        if field in data and isinstance(data[field], str):
            try:
                data[field] = datetime.fromisoformat(data[field])
            except ValueError:
                # fallback: drop invalid date or log warning
                data[field] = None
    return data
