from typing import Annotated, Sequence
from uuid import UUID

from fastapi import Depends, HTTPException
from starlette import status

from src.api.database import SessionDep, user as udb
from src.api.models import UserBase
from src.api.models.models import User


class UserManager:
    def __init__(self, session: SessionDep):
        self.session = session

    def create_user(self, uid: str, email: str, username: str) -> User:
        try:
            user = udb.create_user(uid, email, username, self.session)
            assert user
            return user
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not create user {e}",
            )

    def get_user(self, id: str | UUID) -> User:
        try:
            user = udb.get_user(id, self.session)
            assert user
            return user
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Could not retrieve user {e}",
            )

    def get_user_by_email(self, email) -> User:
        try:
            user = udb.get_user_by_email(email, self.session)
            assert user
            return user
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Could not retrieve user by email {e}",
            )

    def get_user_by_fb(self, uid: str) -> User:
        try:
            user = udb.get_user_by_fb(uid, self.session)
            assert user
            return user
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"user not found  {e}",
            )

    def get_all_users(self, offset: int, limit: int) -> Sequence[User]:
        try:
            return udb.get_all_users(self.session, offset, limit)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not retreive all users",
            )

    def delete_user(self, id: str | UUID) -> bool:
        try:
            udb.delete_user(id, self.session)
            return True
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not delete user {e}",
            )

    def update_user(self, id: str | UUID, data: UserBase) -> User:
        try:
            user = udb.update_user(id, data, self.session)
            assert user
            return user
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not update user {e}",
            )


def get_user_manager(session: SessionDep) -> UserManager:
    return UserManager(session)


UserManagerDependeny = Annotated[UserManager, Depends(get_user_manager)]
