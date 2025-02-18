from sqlalchemy_service import BaseService as BaseRepository
from uuid import UUID

from app.db.tables import Task, TaskItem


class TaskRepository[Table: Task, int](BaseRepository):
    base_table = Task

    async def create(self, model: Task) -> Task:
        self.session.add(model)
        await self._commit()
        self.response.status_code = 201
        return await self.get(model.id)

    async def create_items(self, *models: TaskItem):
        [self.session.add(model) for model in models]
        await self._commit()

    async def list(self, page=None, count=None) -> list[Task]:
        return list(await self._get_list(page=page, count=count))

    async def get(self, model_id: UUID) -> Task:
        return await self._get_one(
            id=model_id,
        )

    async def update(self, model_id: UUID, **fields) -> Task:
        return await self._update(model_id, **fields)

    async def delete(self, model_id: UUID):
        await self._delete(model_id)

