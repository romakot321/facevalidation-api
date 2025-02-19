from fastapi import Depends
import asyncio
import json
from loguru import logger
from aio_pika import connect_robust, Message, Queue
from pydantic import BaseModel

from app.db.rabbitmq import get_rabbitmq_queue, channel_pool
from app.schemas.cv import CVResponse, CVRequest


class CVRepository:
    def __init__(
        self,
        requests_queue: Queue = Depends(get_rabbitmq_queue("cv_requests")),
        responses_queue: Queue = Depends(get_rabbitmq_queue("cv_responses"))
    ):
        self.requests_queue = requests_queue
        self.responses_queue = responses_queue

    async def _send(self, filename: str):
        request = CVRequest(filename=filename).model_dump_json()
        message = Message(
            body=request.encode(),
            reply_to=self.responses_queue.name
        )
        await self.requests_queue.channel.default_exchange.publish(
            message, routing_key="cv_requests"
        )

    async def process_image(self, filename: str):
        await self._send(filename)
        return
        response = await self._receive()
        logger.debug(f"Response: {response}")
        assert all(resp.filename == filename for resp in response), "Not all responses for requested filename: " + str(response)
        return response

    @classmethod
    async def listen_responses(cls, callback):
        async with channel_pool.acquire() as channel:
            queue = await channel.declare_queue(
                "cv_responses", durable=True
            )

            async with queue.iterator() as queue_iter:
                async for response in queue_iter:
                    async with response.process():
                        body = json.loads(response.body)
                        logger.debug(body)
                        body = [CVResponse.model_validate(response) for response in body]
                        await callback(body)

