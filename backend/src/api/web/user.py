# --- Third-Party ---
from fastapi import APIRouter

# --- Internal ---
from src.api.models import UserBase
from src.api.service.user import UserManagerDependeny
from src.api.models.models import User
from src.api.core.logging import logger
from src.api.dependencies import FireBaseToken
from fastapi import HTTPException
from starlette import status
from src.firebase.core import initialize_firebase_app

router = APIRouter(prefix="/users", tags=["users"])
initialize_firebase_app()


@router.post("/")
async def create_user(
    user_manager: UserManagerDependeny,
    fb_token: FireBaseToken,
    data: UserBase,
) -> User:
    """
    Create a new user in the system.

    Args:
        user_manager (UserManagerDependeny): Dependency providing user management operations.
        data (UserBase): Incoming user registration data (email, fb_id, etc.).

    Returns:
        User: The newly created user object.
    """

    # Check if the user already exist in the database
    try:
        existing_user = user_manager.get_user_by_fb(uid=fb_token["uid"])
        if existing_user:
            logger.info(f"[DB] User already exists: {existing_user.fb_id}")
            return existing_user
        # Other wise create a user
        logger.info(
            "Creating user with email='%s' and fb_id='%s'",
            data.email,
        )
        created_user = user_manager.create_user(
            uid=fb_token["uid"],
            email=data.email,
            username=data.email,
        )

        logger.info("User created successfully: uid='%s'", created_user.id)
        return created_user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occured while creating the user {e}",
        )


@router.get("/")
async def get_user(
    user_manager: UserManagerDependeny,
    token: FireBaseToken,
) -> User:
    """
    Retrieve a user by their unique ID.

    Args:
        user_manager (UserManagerDependeny): User management service.
        id (str): The user ID to retrieve.

    Returns:
        User: The user with the specified ID.
    """

    logger.info(f"Got token {token}")
    try:

        user = user_manager.get_user_by_fb(token["uid"])

        logger.info("Retrieved user: uid='%s', email='%s'", user.id, user.email)
        return user
    except HTTPException as e:
        if "user not found" in e.detail.lower():
            logger.info("[DB] User not found — creating new one.")
            try:
                user = user_manager.create_user(
                    uid=token["uid"], email=token["email"], username=""
                )
                logger.info("[DB] User not found — creating new one.")
                assert user
                return user
            except Exception as err:
                logger.error(f"[DB] Failed to auto-create user: {err}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to auto-create user.",
                )
        else:
            raise


@router.delete("/")
async def delete_user(
    user_manager: UserManagerDependeny,
    token: FireBaseToken,
):
    """
    Delete a user by their ID.

    Args:
        user_manager (UserManagerDependeny): User management service.
        id (str): User ID to delete.

    Returns:
        dict: Success message.
    """
    logger.warning("Deleting user with id='%s'", id)
    user = user_manager.get_user_by_fb(token["uid"])
    assert user.id

    user_manager.delete_user(user.id)

    logger.info("User successfully deleted: id='%s'", id)
    return {"detail": "user deleted"}


@router.put("/")
async def update_user(
    user_manager: UserManagerDependeny,
    token: FireBaseToken,
    data: UserBase,
) -> User:
    """
    Update an existing user's information.

    Args:
        user_manager (UserManagerDependeny): User service handler.
        id (str): ID of the user to update.
        data (UserBase): Updated user information.

    Returns:
        User: The updated user object.
    """
    logger.info("Updating user id='%s' with new email='%s'", id, data.email)
    user = user_manager.get_user_by_fb(token["uid"])

    updated_user = user_manager.update_user(user.id, data)

    logger.info("User updated successfully: id='%s'", id)
    return updated_user
