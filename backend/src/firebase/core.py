from pathlib import Path
import json
from firebase_admin import credentials
import firebase_admin
from functools import lru_cache
from src.api.core import logger
from src.api.core.config import get_settings

app_settings = get_settings()


@lru_cache
def initialize_firebase_app():
    if not app_settings.FIREBASE_CRED:
        raise ValueError("Firebase Credentials Not Found")
    try:
        if app_settings.MODE == "production":
            cred = json.loads(app_settings.FIREBASE_CRED)
        else:
            root_path = Path(__file__).parents[3]
            cred = (root_path / app_settings.FIREBASE_CRED).resolve()
            logger.debug("Root Path is {cred}")
    except Exception as e:
        raise ValueError(f"There was an error loading credentials {str(e)}")

    try:
        cred = credentials.Certificate(cred)
        bucket_name = app_settings.STORAGE_BUCKET
        firebase_admin.initialize_app(cred, {"storageBucket": bucket_name})
    except Exception as e:
        raise ValueError(f"Could not initialize creditionals error {str(e)}")
