#!/usr/bin/env python3


# This is a demo of detecting eye status from the users camera. If the users eyes are closed for EYES_CLOSED seconds, the system will start printing out "EYES CLOSED"
# to the terminal until the user presses and holds the spacebar to acknowledge

# this demo must be run with sudo privileges for the keyboard module to work

# PLEASE NOTE: This example requires OpenCV (the `cv2` library) to be installed only to read from your webcam.
# OpenCV is *not* required to use the face_recognition library. It's only required if you want to run this
# specific demo. If you have trouble installing it, try any of the other demos that don't require it instead.

# imports
import os
import face_recognition
import cv2
import pika
from scipy.spatial import distance as dist
import dataclasses
import json

images_directory = "images/"
rabbitmq_host = os.getenv("RABBITMQ_HOST")


@dataclasses.dataclass
class Response:
    filename: str
    left_eye_close: float
    right_eye_close: float
    face_location: list[int]
    image_size: list[int]


@dataclasses.dataclass
class Request:
    filename: str


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


def recognize(filename: str) -> list[Response]:
    img = face_recognition.load_image_file(images_directory + filename)
    responses = []
    face_location_list = face_recognition.face_locations(img)
    face_landmarks_list = face_recognition.face_landmarks(img)

    # get eyes
    for landmark, location in zip(face_landmarks_list, face_location_list):
        left_eye = landmark['left_eye']
        right_eye = landmark['right_eye']

        eye_left = get_eye(left_eye)
        eye_right = get_eye(right_eye)
        responses.append(
            Response(
                filename=filename,
                left_eye_close=eye_left,
                right_eye_close=eye_right,
                face_location=location,
                image_size=img.shape[:2]
            )
        )
    return responses


def callback(ch, method, properties, body):
    print("[*] Receive: " + str(body))
    try:
        request = Request(**json.loads(body))
    except Exception:
        return
    responses = recognize(request.filename)
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

