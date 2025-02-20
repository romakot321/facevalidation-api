from sqlalchemy_service import BaseService as BaseRepository

from app.db.tables import TaskItem


class TaskItemRepository[Table: TaskItem, int](BaseRepository):
    base_table = TaskItem

    async def create(self, model: TaskItem) -> TaskItem:
        self.session.add(model)
        await self._commit()
        self.response.status_code = 201
        return await self.get(model.id)

    async def list(self, page=None, count=None) -> list[TaskItem]:
        return list(await self._get_list(page=page, count=count))

    async def get(self, model_id: int) -> TaskItem:
        return await self._get_one(
            id=model_id,
        )

    async def update(self, model_id: int, **fields) -> TaskItem:
        return await self._update(model_id, **fields)

    async def delete(self, model_id: int):
        await self._delete(model_id)

