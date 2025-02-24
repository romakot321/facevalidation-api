from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile
from uuid import UUID

from app.repositories.cv import CVRepository
from app.schemas.task import TaskSchema
from app.services.task import TaskService
from . import validate_api_token


router = APIRouter(prefix="/api/task", tags=["Face Validation Task"])


@router.post("", response_model=TaskSchema)
async def create_validation_task(
        background_tasks: BackgroundTasks,
        file: list[UploadFile],
        cv_repository: CVRepository = Depends(),
        service: TaskService = Depends(TaskService)
):
    model = await service.create()
    for i, f in enumerate(file):
        background_tasks.add_task(service.send, model.id, await f.read(), i, cv_repository)
    return model


@router.get("/{task_id}")
async def get_task_status(
        task_id: UUID,
        service: TaskService = Depends(TaskService)
):
    return await service.get(task_id)

