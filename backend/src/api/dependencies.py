from typing import Annotated, Literal

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin.auth import verify_id_token
from starlette import status

from src.api.core.config import AppSettings, get_settings


StorageType = Literal["local", "cloud"]


def get_app_settings() -> AppSettings:
    """
    Dependency that provides application settings from environment or config file.
    """
    return get_settings()


SettingDependency = Annotated[AppSettings, Depends(get_app_settings)]


def get_storage_type(
    settings: SettingDependency,
) -> StorageType:
    """
    Dependency that extracts the storage type from the global app settings.
    """
    return settings.STORAGE_SERVICE


# Type alias for injecting storage type directly
StorageTypeDep = Annotated[StorageType, Depends(get_storage_type)]





bearer_scheme = HTTPBearer(auto_error=False)


def get_firebase_user_from_token(
    token: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> dict | None:
    try:
        if not token:
            raise ValueError("No Token")
        user = verify_id_token(token.credentials)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Not logged in or Invalid credentials {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


FireBaseToken = Annotated[dict, Depends(get_firebase_user_from_token)]
