from io import BytesIO
import math
import os
import face_recognition
import cv2
import pika
from scipy.spatial import distance as dist
import dataclasses
import json
from PIL import Image
import numpy as np
from typing import Union, List

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


def define_glasses(image_buffer: BytesIO, landmarks: dict):
    xmin = min(landmarks['nose_tip'], key=lambda i: i[0])[0]
    xmax = max(landmarks['nose_tip'], key=lambda i: i[0])[0]
    ymin = min(landmarks['left_eyebrow'], key=lambda i: i[1])[1]
    ymax = max(landmarks['nose_bridge'], key=lambda i: i[1])[1]

    img2 = Image.open(image_buffer)
    img2 = img2.crop((xmin, ymin, xmax, ymax))

    img_blur = cv2.GaussianBlur(np.array(img2),(3,3), sigmaX=0, sigmaY=0)
    edges = cv2.Canny(image=img_blur, threshold1=100, threshold2=200)

    edges_center = edges.T[(int(len(edges.T)/2))]

    return 255 in edges_center


def get_rotation(face_landmarks) -> float:
    """if abs(rotation) > 0.3, then face is rotated too much"""
    left, right = (min(face_landmarks['chin'], key=lambda i: i[0]), max(face_landmarks['chin'], key=lambda i: i[0]))
    left_eye_left = min(face_landmarks['left_eye'], key=lambda i: i[0])
    right_eye_right = max(face_landmarks['right_eye'], key=lambda i: i[1])
    width = right[0] - left[0]
    distance_left = ((left_eye_left[0] - left[0]) ** 2 + (left_eye_left[1] - left[1]) ** 2) ** 0.5 / width
    distance_right = ((right_eye_right[0] - right[0]) ** 2 + (right_eye_right[1] - right[1]) ** 2) ** 0.5 / width
    rotate = 1 - distance_left / distance_right
    return rotate


def recognize(filename: str, task_id: str) -> List[Response]:
    responses = []
    with open(images_directory + filename, 'rb') as f:
        buffer = BytesIO(f.read())
    img = face_recognition.load_image_file(buffer)
    image_width, image_height, _ = img.shape

    face_landmarks_list = face_recognition.face_landmarks(img)
    if not face_landmarks_list:
        return [Response(filename=filename, task_id=task_id, error="Face not found")]

    for landmark in face_landmarks_list:
        left_eye = landmark['left_eye']
        right_eye = landmark['right_eye']

        left = min(landmark['chin'], key=lambda i: i[0])
        right = max(landmark['chin'], key=lambda i: i[0])
        top = min(landmark['left_eyebrow'] + face_landmarks_list[0]['right_eyebrow'], key=lambda i: i[1])
        bottom = max(landmark['chin'], key=lambda i: i[1])

        eye_left = get_eye(left_eye)
        eye_right = get_eye(right_eye)
        glasses = define_glasses(buffer, landmark)
        rotation = get_rotation(landmark)
        responses.append(
            Response(
                filename=filename,
                left_eye_close=eye_left,
                right_eye_close=eye_right,
                face_location=[top[1], right[0], bottom[1], left[0]],  # Response in face_recognition format
                image_size=img.shape[:2],
                glasses=glasses,
                rotation=rotation,
                task_id=task_id
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
        exchange='',
        routing_key=properties.reply_to,
        body=json.dumps(responses, cls=EnhancedJSONEncoder)
    )


def consume_json_messages():
    # Connect to RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitmq_host))
    channel = connection.channel()

    # Declare the same queue
    channel.queue_declare(queue='cv_requests', durable=True)

    # Set up the consumer
    channel.basic_consume(queue='cv_requests', on_message_callback=callback, auto_ack=True)

    print('Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()


if __name__ == "__main__":
    consume_json_messages()

