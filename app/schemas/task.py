from uuid import UUID
from pydantic import BaseModel, ConfigDict, computed_field


class TaskItemSchema(BaseModel):
    id: int | None = None
    left_eye_close: float
    right_eye_close: float
    face_left: int
    face_top: int
    face_bottom: int
    face_right: int
    image_width: int
    image_height: int
    with_glasses: bool

    @computed_field
    @property
    def is_face_small(self) -> bool:
        return (self.face_right - self.face_left) / self.image_width < 0.05

    @computed_field
    @property
    def is_eyes_closed(self) -> bool:
        return self.left_eye_close < 0.2 and self.right_eye_close < 0.2

    model_config = ConfigDict(from_attributes=True)


class TaskSchema(BaseModel):
    id: UUID
    items: list[TaskItemSchema]
    error: str | None = None

    model_config = ConfigDict(from_attributes=True)

