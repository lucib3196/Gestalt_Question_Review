from typing import Type, TypeVar
from sqlmodel import SQLModel, select
from sqlalchemy import func
from src.api.database.database import SessionDep
from sqlalchemy.exc import SQLAlchemyError
from src.api.core import logger
from sqlalchemy.inspection import inspect
from typing import Dict
from sqlalchemy.orm.properties import RelationshipProperty
from sqlalchemy.orm.exc import UnmappedInstanceError
from typing import List, Any

T = TypeVar("T", bound=SQLModel)


def create_or_resolve(
    target_cls: Type[T],
    target_value: str,
    session: SessionDep,
    lookup_field: str = "name",
    create: bool = True,
):

    try:
        getattr(target_cls, lookup_field)
    except Exception as e:
        raise ValueError(f"{lookup_field} is not a property of {target_cls}")

    stmt = select(target_cls).where(
        func.lower(getattr(target_cls, lookup_field)) == target_value
    )
    result = session.exec(stmt).first()
    if result:
        return result, True
    if create:
        try:
            obj: SQLModel = target_cls(**{lookup_field: target_value.strip()})
            session.add(obj)
            session.commit()
            session.refresh(obj)
            return obj, False
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"[DB] could not create {target_cls} {e}")
            raise ValueError(f"[DB] failed to create {target_cls} an error occured {e}")
    raise ValueError(
        f"Object of type '{target_cls.__name__}' with {lookup_field}='{target_value}' not found "
        f"and create_field=False"
    )


def get_all_model_relationships(model: Type[SQLModel]) -> Dict[str, str]:
    mapper = inspect(model)
    relationships = {}
    for name, rel in mapper.relationships.items():
        relationships[name] = rel.mapper.class_.__name__
    return relationships


def get_all_model_relationship_data(
    model: SQLModel, base_model: Type[SQLModel], excluded_relationship: List[str] = []
) -> Dict[str, Any]:
    all_relationships = get_all_model_relationships(base_model)
    data = {}
    for r in all_relationships:
        if r in excluded_relationship:
            continue
        data[r] = getattr(model, r)
    return data


def is_relationship(model: Type[SQLModel], attr_name: str) -> bool:
    """True if model.attr_name is a relationship."""
    try:
        prop = inspect(model).get_property(attr_name)
        return isinstance(prop, RelationshipProperty)
    except Exception as e:
        return False
