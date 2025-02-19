from pydantic import BaseModel


class CVResponse(BaseModel):
    filename: str
    left_eye_close: float
    right_eye_close: float
    face_location: list[int]
    image_size: list[int]
    glasses: bool


class CVRequest(BaseModel):
    filename: str
