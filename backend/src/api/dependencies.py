from fastapi import Depends
from src.api.service.question_manager import QuestionManager
from src.api.core import logger
from src.api.core.config import get_settings
from src.api.service.storage import FireCloudStorageService, LocalStorageService
from typing import Annotated

settings = get_settings()

def get_question_manager() -> QuestionManager:
    if settings.STORAGE_SERVICE == "cloud":
        if not (settings.FIREBASE_CRED and settings.STORAGE_BUCKET):
            raise ValueError("Settings for Cloud Storage not Set")
        storage_service = FireCloudStorageService(
            cred_path=settings.FIREBASE_CRED,
            bucket_name=settings.STORAGE_BUCKET,
            base_name="UCR_Questions",
        )

    else:
        storage_service = LocalStorageService(settings.QUESTIONS_PATH)
    logger.info(f"Question manager set to {settings.STORAGE_SERVICE}")
    logger.info("Initialized Question Manager Success ")
    return QuestionManager(storage_service, storage_type=settings.STORAGE_SERVICE)


QuestionManagerDependency = Annotated[QuestionManager, Depends(get_question_manager)]
