from uuid import UUID
from fastapi import Depends
from loguru import logger

from sqlalchemy_service.base_db.base import get_session as get_db_session

from app.db.tables import Task, TaskItem
from app.repositories.image import ImageRepository
from app.repositories.cv import CVRepository
from app.repositories.task import TaskRepository
from app.repositories.task_item import TaskItemRepository
from app.schemas.cv import CVResponse
from app.schemas.task import TaskItemSchema, TaskItemShortSchema, TaskSchema, TaskShortSchema


class TaskService:
    def __init__(
            self,
            task_repository: TaskRepository = Depends(),
            task_item_repository: TaskItemRepository = Depends(),
            image_repository: ImageRepository = Depends()
    ):
        self.task_repository = task_repository
        self.task_item_repository = task_item_repository
        self.image_repository = image_repository

    async def item_vote(self, item_id: int, value: bool):
        await self.task_item_repository.update(item_id, is_good=value)

    async def create(self) -> TaskSchema:
        model = Task()
        return await self.task_repository.create(model)

    async def get_list(self, count: int = 100, page: int = 0) -> list[TaskShortSchema]:
        models = await self.task_repository.list(page=page, count=count)
        return [TaskShortSchema.model_validate(model) for model in models]

    async def send(self, task_id: UUID, image_raw: bytes, image_index: int, cv_repository: CVRepository):
        image_filename = f"{task_id}:{image_index}"
        self.image_repository.store(image_raw, image_filename)

        try:
            await cv_repository.process_image(image_filename, str(task_id))
        except Exception as e:
            logger.exception(e)
            await self.task_repository.update(task_id, error=str(e))
            return

    async def _save_cv_response(self, response: list[CVResponse]):
        if not response:
            return
        task_items = [
            (
                TaskItemSchema(left_eye_close=face.left_eye_close, right_eye_close=face.right_eye_close,
                           face_left=face.face_location[3], face_top=face.face_location[0],
                           face_right=face.face_location[1], face_bottom=face.face_location[2],
                           image_width=face.image_size[0], image_height=face.image_size[1],
                           with_glasses=face.glasses, task_id=face.task_id,
                           image_index=int(face.filename.split(":")[1]),
                           error=face.error)
                if face.image_size is not None else
                TaskItemSchema(task_id=face.task_id, image_index=int(face.filename.split(":")[1]), error=face.error)
            )
            for face in response
        ]
        task_items = [TaskItem(**schema.model_dump()) for schema in task_items]
        logger.debug(f"Saving {len(task_items)} items")
        await self.task_repository.create_items(*task_items)

    async def get(self, task_id: UUID) -> TaskSchema:
        model = await self.task_repository.get(task_id)
        return TaskSchema.model_validate(model)

    @classmethod
    async def save_cv_response(cls, response: list[CVResponse]):
        session_getter = get_db_session()
        session = await anext(session_getter)
        self = cls(image_repository=None, task_repository=TaskRepository(session=session))

        await self._save_cv_response(response)

        try:
            await anext(session_getter)
            await session.close()
        except StopAsyncIteration:
            pass

