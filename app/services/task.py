from uuid import UUID
from fastapi import Depends
from loguru import logger

from sqlalchemy_service.base_db.base import get_session as get_db_session

from app.db.tables import Task, TaskItem
from app.repositories.image import ImageRepository
from app.repositories.cv import CVRepository
from app.repositories.task import TaskRepository
from app.schemas.cv import CVResponse
from app.schemas.task import TaskItemSchema, TaskSchema


class TaskService:
    def __init__(
            self,
            cv_repository: CVRepository = Depends(),
            task_repository: TaskRepository = Depends(),
            image_repository: ImageRepository = Depends()
    ):
        self.cv_repository = cv_repository
        self.task_repository = task_repository
        self.image_repository = image_repository

    async def create(self) -> TaskSchema:
        logger.debug("Creating task model...")
        model = Task()
        return await self.task_repository.create(model)

    async def send(self, task_id: UUID, image_raw: bytes):
        filename = str(task_id)
        self.image_repository.store(image_raw, filename)

        try:
            response = await self.cv_repository.process_image(filename)
        except Exception as e:
            logger.exception(e)
            await self.task_repository.update(task_id, error=str(e))
            return

    async def _save_cv_response(self, response: list[CVResponse]):
        if not response:
            return
        task_items = [
            TaskItemSchema(left_eye_close=face.left_eye_close, right_eye_close=face.right_eye_close,
                           face_left=face.face_location[3], face_top=face.face_location[0],
                           face_right=face.face_location[1], face_bottom=face.face_location[2],
                           image_width=face.image_size[0], image_height=face.image_size[1],
                           with_glasses=face.glasses)
            for face in response
        ]
        task_items = [TaskItem(**schema.model_dump(), task_id=response[0].filename) for schema in task_items]
        logger.debug(f"Saving {len(task_items)} items")
        await self.task_repository.create_items(*task_items)

    async def get(self, task_id: UUID) -> TaskSchema:
        model = await self.task_repository.get(task_id)
        return TaskSchema.model_validate(model)

    @classmethod
    async def save_cv_response(cls, response: list[CVResponse]):
        logger.debug("Getting session...")
        session_getter = get_db_session()
        session = await anext(session_getter)
        self = cls(cv_repository=None, image_repository=None, task_repository=TaskRepository(session=session))

        logger.debug("Start cv saving...")
        await self._save_cv_response(response)
        logger.debug("CV Saved")

        try:
            await anext(session_getter)
            await session.close()
        except StopAsyncIteration:
            pass

