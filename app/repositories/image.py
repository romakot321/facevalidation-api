import os
import pathlib


class ImageRepository:
    IMAGES_PATH = pathlib.Path(os.getenv("IMAGES_PATH", "images"))

    def store(self, body: bytes, filename: str):
        with open(self.IMAGES_PATH / filename, 'wb') as f:
            f.write(body)

