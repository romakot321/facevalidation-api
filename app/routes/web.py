from uuid import UUID
from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from loguru import logger
from base64 import b64encode

from app.repositories.image import ImageRepository
from app.services.task import TaskService

router = APIRouter(prefix="/panel")
templates = Jinja2Templates(directory="templates")


@router.get("", response_class=HTMLResponse)
async def index_page(
        request: Request,
        task_service: TaskService = Depends()
):
    tasks = await task_service.get_list()
    return templates.TemplateResponse("index.html", {"request": request, "tasks": tasks})


@router.get("/{task_id}", response_class=HTMLResponse)
async def details_page(
        request: Request,
        task_id: UUID,
        task_service: TaskService = Depends(),
        image_repository: ImageRepository = Depends()
):
    model = await task_service.get(task_id)
    images = []
    for item in model.items:
        image_buffer = image_repository.get(str(model.id) + ":" + str(item.image_index))
        image_buffer = image_repository.draw_rect(
            image_buffer, (item.face_left, item.face_top, item.face_right, item.face_bottom)
        )
        image_encoded = b64encode(image_buffer.getvalue()).decode("utf-8")
        images.append(image_encoded)
    return templates.TemplateResponse("details.html", {"request": request, "task": model, "images": images})


@router.post("/{task_id}/vote/{item_id}")
async def vote_for_result(
        task_id: UUID,
        item_id: int,
        value: bool = Query(),
        task_service: TaskService = Depends()
):
    await task_service.item_vote(item_id, value)

