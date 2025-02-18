from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile
from uuid import UUID

from app.services.task import TaskService
from . import validate_api_token


router = APIRouter(prefix="/api/task", tags=["Face Validation Task"])


@router.post("")
async def create_validation_task(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(),
        service: TaskService = Depends()
):
    model = await service.create()
    background_tasks.add_task(service.send, model.id, await file.read())
    return model


@router.get("/{task_id}")
async def get_task_status(
        task_id: UUID,
        service: TaskService = Depends()
):
    return await service.get(task_id)

