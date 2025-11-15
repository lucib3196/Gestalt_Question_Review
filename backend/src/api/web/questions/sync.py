from src.api.service import sync
from fastapi.routing import APIRouter
from src.api.models import *
from src.api.models.sync_models import *
from src.api.service.question.question_manager import QuestionManagerDependency
from src.api.service.storage_manager import StorageDependency
from fastapi import HTTPException


router = APIRouter(prefix="/questions", tags=["questions", "sync", "dev", "local"])


@router.post("/check_unsync", response_model=List[UnsyncedQuestion])
async def view_local(
    qm: QuestionManagerDependency, storage: StorageDependency
) -> Sequence[UnsyncedQuestion]:
    try:
        return await sync.check_local_unsync(storage, qm)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check sync {e}")


@router.post("/sync_questions")
async def sync_questions(
    qm: QuestionManagerDependency, storage: StorageDependency
) -> SyncMetrics:
    try:
        return await sync.sync_questions(
            qm,
            storage,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to  sync {e}")


@router.post("/prune_missing_questions")
async def prune_missing_questions(
    qm: QuestionManagerDependency, storage: StorageDependency
) -> FolderCheckMetrics:
    try:
        return await sync.prune_questions(qm, storage)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to prune {e}")
