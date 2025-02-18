import aio_pika
from aio_pika.abc import AbstractRobustConnection
from aio_pika.pool import Pool
import os

rabbitmq_host = os.getenv("RABBITMQ_HOST")


async def _get_connection() -> AbstractRobustConnection:
    return await aio_pika.connect_robust(f"amqp://guest:guest@{rabbitmq_host}/")

connection_pool: Pool = Pool(_get_connection, max_size=2)

async def _get_channel() -> aio_pika.Channel:
    async with connection_pool.acquire() as connection:
        return await connection.channel()

channel_pool: Pool = Pool(_get_channel, max_size=10)


async def get_rabbitmq_channel() -> aio_pika.Channel:
    async with channel_pool.acquire() as channel:
        yield channel


def get_rabbitmq_queue(queue_name: str):

    async def _get():
        async with channel_pool.acquire() as channel:
            queue = await channel.declare_queue(
                queue_name, durable=True
            )
            yield queue

    return _get

