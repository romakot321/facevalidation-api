from uuid import UUID
from pydantic import BaseModel, ConfigDict, computed_field


class TaskItemShortSchema(BaseModel):
    id: int | None = None
    left_eye_close: float | None = None
    right_eye_close: float | None = None
    is_eyes_closed: bool | None = None
    is_face_small: bool | None = None
    with_glasses: bool | None = None
    is_rotation_huge: bool | None = None
    image_index: int | None = None
    error: str | None = None
    is_good: bool | None = None

    model_config = ConfigDict(from_attributes=True)


class TaskShortSchema(BaseModel):
    id: UUID
    items: list[TaskItemShortSchema]
    error: str | None = None

    model_config = ConfigDict(from_attributes=True)


class TaskItemSchema(BaseModel):
    id: int | None = None
    left_eye_close: float | None = None
    right_eye_close: float | None = None
    face_left: int | None = None
    face_top: int | None = None
    face_bottom: int | None = None
    face_right: int | None = None
    image_width: int | None = None
    image_height: int | None = None
    with_glasses: bool | None = None
    task_id: UUID | str | None = None
    image_index: int | None = None
    rotation: float | None = None
    error: str | None = None
    is_good: bool | None = None

    @computed_field
    @property
    def is_face_small(self) -> bool | None:
        if self.face_right is None or self.face_left is None or self.image_width is None:
            return None
        return (self.face_right - self.face_left) / self.image_width < 0.05

    @computed_field
    @property
    def is_eyes_closed(self) -> bool | None:
        if self.left_eye_close is None or self.right_eye_close is None:
            return None
        return self.left_eye_close < 0.2 and self.right_eye_close < 0.2

    @computed_field
    @property
    def is_rotation_huge(self) -> bool | None:
        if self.rotation is None:
            return None
        return abs(self.rotation) > 0.4

    model_config = ConfigDict(from_attributes=True)


class TaskSchema(BaseModel):
    id: UUID
    items: list[TaskItemSchema]
    error: str | None = None

    model_config = ConfigDict(from_attributes=True)

