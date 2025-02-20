from pydantic import BaseModel


class CVResponse(BaseModel):
    filename: str
    task_id: str
    left_eye_close: float | None = None
    right_eye_close: float | None = None
    face_location: list[int] | None = None
    image_size: list[int] | None = None
    glasses: bool | None = None
    error: str | None = None


class CVRequest(BaseModel):
    filename: str
    task_id: str

