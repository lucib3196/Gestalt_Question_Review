import pytest
import src.api.database.user as user_db

from src.api.models import UserBase
from src.api.models.models import UserRole


@pytest.fixture
def user_data():
    return {"uid": "1234", "email": "test@email.com", "username": "user"}


@pytest.fixture
def create_user(user_data, db_session):
    user = user_db.create_user(
        uid=user_data["uid"],
        email=user_data["email"],
        username=user_data["username"],
        session=db_session,
    )
    return user


def test_user_create(create_user):
    user = create_user
    assert user


def test_get_user(create_user, db_session):
    cuser = create_user
    ruser = user_db.get_user(cuser.id, db_session)
    assert ruser
    assert cuser == ruser


def test_get_user_by_email(create_user, user_data, db_session):
    cuser = create_user
    ruser = user_db.get_user_by_email(user_data["email"], db_session)
    assert cuser == ruser


def test_get_user_by_fb(create_user, user_data, db_session):
    cuser = create_user
    ruser = user_db.get_user_by_fb(user_data["uid"], db_session)
    assert cuser == ruser


def test_delete_user(create_user, db_session):
    cuser = create_user
    user_db.delete_user(cuser.id, db_session)
    ruser = user_db.get_user(cuser.id, db_session)
    assert ruser is None


def test_update_user(create_user, db_session):
    update_data = UserBase(
        username="My new username", email="newEmail@gmail.com", role=UserRole.TEACHER
    )
    cuser = create_user
    update = user_db.update_user(cuser.id, data=update_data, session=db_session)
    assert update
    assert update.id == cuser.id
    print("This is the created user", update)
