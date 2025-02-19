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
):
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/{task_id}", response_class=HTMLResponse)
async def details_page(
        request: Request,
        task_id: UUID,
        task_service: TaskService = Depends(),
        image_repository: ImageRepository = Depends()
):
    model = await task_service.get(task_id)
    image_buffer = image_repository.get(str(model.id))
    if model.items:
        for item in model.items:
            image_buffer = image_repository.draw_rect(
                image_buffer, (item.face_left, item.face_top, item.face_right, item.face_bottom)
            )
    image_encoded = b64encode(image_buffer.getvalue()).decode("utf-8")
    return templates.TemplateResponse("details.html", {"request": request, "task": model, "image": image_encoded})

