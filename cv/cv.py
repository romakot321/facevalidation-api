from io import BytesIO
import math
import os
import face_alignment
import cv2
import pika
from scipy.spatial import distance as dist
import dataclasses
import json
from PIL import Image
import numpy as np
from typing import Union, List
import collections
import torch

images_directory = "images/"
rabbitmq_host = os.getenv("RABBITMQ_HOST")


@dataclasses.dataclass
class Response:
    filename: str
    task_id: str
    error: Union[str, None] = None
    left_eye_close: Union[float, None] = None
    right_eye_close: Union[float, None] = None
    face_location: Union[List[int], None] = None
    image_size: Union[List[int], None] = None
    rotation: Union[float, None] = None
    glasses: Union[bool, None] = None


@dataclasses.dataclass
class Request:
    filename: str
    task_id: str


pred_types = {
    "face": slice(0, 17),
    "eyebrow1": slice(17, 22),
    "eyebrow2": slice(22, 27),
    "nose": slice(27, 31),
    "nostril": slice(31, 36),
    "eye1": slice(36, 42),
    "eye2": slice(42, 48),
    "lips": slice(48, 60),
    "teeth": slice(60, 68),
}

if os.getenv("CPU"):
    detector = face_alignment.FaceAlignment(
        face_alignment.LandmarksType.TWO_D,
        device="cpu",
        flip_input=True,
        face_detector="blazeface",
    )
else:
    detector = face_alignment.FaceAlignment(
        face_alignment.LandmarksType.TWO_D,
        device="cuda",
        dtype=torch.bfloat16,
        flip_input=True,
        face_detector="blazeface",
    )


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


def get_eye(eye):
    # compute the euclidean distances between the two sets of
    # vertical eye landmarks (x, y)-coordinates
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])

    # compute the euclidean distance between the horizontal
    # eye landmark (x, y)-coordinates
    C = dist.euclidean(eye[0], eye[3])

    # compute the eye aspect ratio
    eye = (A + B) / (2.0 * C)

    # return the eye aspect ratio
    return eye


def define_glasses(image_buffer: BytesIO, landmarks: np.ndarray):
    xmin = min(landmarks[pred_types["nostril"]], key=lambda i: i[0])[0]
    xmax = max(landmarks[pred_types["nostril"]], key=lambda i: i[0])[0]
    ymin = min(landmarks[pred_types["face"]], key=lambda i: i[1])[1]
    ymax = min(landmarks[pred_types['nose']], key=lambda i: i[1])[1]

    img2 = Image.open(image_buffer)
    img2 = img2.crop((xmin, ymin, xmax, ymax))

    img_blur = cv2.GaussianBlur(np.array(img2), (3, 3), sigmaX=0, sigmaY=0)
    edges = cv2.Canny(image=img_blur, threshold1=100, threshold2=200)

    edges_center = edges.T[(int(len(edges.T) / 2))]

    return 255 in edges_center


def get_rotation(landmarks) -> float:
    """if abs(rotation) > 0.17, then face is profile. If abs(rotation) > 0.045, then face is half-profile"""
    face_points = landmarks[pred_types["face"]]
    left = face_points[0]
    right = face_points[-1]
    width = (
        max(landmarks, key=lambda i: i[0])[0] - min(landmarks, key=lambda i: i[0])[0]
    )

    distance = ((left[0] - right[0]) ** 2 + (left[1] - right[1]) ** 2) ** 0.5
    return 1 - distance / width


def recognize(filename: str, task_id: str) -> List[Response]:
    responses = []
    with open(images_directory + filename, "rb") as f:
        buffer = BytesIO(f.read())
    img = np.array(Image.open(buffer))
    image_width, image_height, _ = img.shape

    face_landmarks_list = detector.get_landmarks(img)
    if not face_landmarks_list:
        return [Response(filename=filename, task_id=task_id, error="Face not found")]

    for landmark in face_landmarks_list:
        left_eye = landmark[pred_types["eye1"]]
        right_eye = landmark[pred_types["eye2"]]

        left = min(landmark, key=lambda i: i[0])
        right = max(landmark, key=lambda i: i[0])
        top = min(landmark, key=lambda i: i[1])
        bottom = max(landmark, key=lambda i: i[1])

        eye_left = get_eye(left_eye)
        eye_right = get_eye(right_eye)
        glasses = define_glasses(buffer, landmark)
        rotation = get_rotation(landmark)
        responses.append(
            Response(
                filename=filename,
                left_eye_close=float(eye_left),
                right_eye_close=float(eye_right),
                face_location=[
                    int(top[1]),
                    int(right[0]),
                    int(bottom[1]),
                    int(left[0]),
                ],  # Response in face_recognition format
                image_size=img.shape[:2],
                glasses=glasses,
                rotation=float(rotation),
                task_id=task_id,
            )
        )
    return responses


def callback(ch, method, properties, body):
    print("[*] Receive: " + str(body))
    try:
        request = Request(**json.loads(body))
    except Exception:
        return
    responses = recognize(request.filename, request.task_id)
    print("[*] Response: " + str(responses))
    ch.basic_publish(
        exchange="",
        routing_key=properties.reply_to,
        body=json.dumps(responses, cls=EnhancedJSONEncoder),
    )


def consume_json_messages():
    # Connect to RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitmq_host))
    channel = connection.channel()

    # Declare the same queue
    channel.queue_declare(queue="cv_requests", durable=True)

    # Set up the consumer
    channel.basic_consume(
        queue="cv_requests", on_message_callback=callback, auto_ack=True
    )

    print("Waiting for messages. To exit press CTRL+C")
    channel.start_consuming()


if __name__ == "__main__":
    consume_json_messages()
