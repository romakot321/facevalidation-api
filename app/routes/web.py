from uuid import UUID
from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from loguru import logger

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
        task_service: TaskService = Depends()
):
    model = await task_service.get(task_id)
    return templates.TemplateResponse("details.html", {"request": request, "task": model})

