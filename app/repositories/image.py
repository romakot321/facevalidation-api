from io import BytesIO
import os
import pathlib

from PIL import Image, ImageDraw


class ImageRepository:
    IMAGES_PATH = pathlib.Path(os.getenv("IMAGES_PATH", "images"))

    def store(self, body: bytes, filename: str):
        with open(self.IMAGES_PATH / filename, 'wb') as f:
            f.write(body)

    def get(self, filename: str) -> BytesIO:
        with open(self.IMAGES_PATH / filename, 'rb') as f:
            return BytesIO(f.read())

    def draw_rect(self, buffer: BytesIO, rect: tuple[int, int, int, int]) -> BytesIO:
        im = Image.open(buffer)
        draw = ImageDraw.Draw(im)
        draw.rectangle((rect[:2], rect[2:]), outline="green", width=7)
        new_buffer = BytesIO()
        im.save(new_buffer, 'png')
        return new_buffer

