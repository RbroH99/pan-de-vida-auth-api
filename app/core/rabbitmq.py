"""
RabbitMQ middlewares
"""
import json

import aio_pika

from app.settings import RABBITMQ_URL

async def get_rabbitmq_connection():
    connection = await aio_pika.connect_robust(
        RABBITMQ_URL
    )
    return connection


async def send_user_notification(queue, user_info):
    """Sends id and email of user to RabbitMQ when created."""
    connection = await get_rabbitmq_connection()
    channel = await connection.channel()

    queue = await channel.declare_queue(queue, durable=True)

    user_info = json.dumps(user_info)
    message = aio_pika.Message(body=user_info.encode())
    await channel.default_exchange.publish(
        message,
        routing_key=queue.name
    )
    print(f"AUTH API Sent {json.loads(user_info)['email']}")
    await connection.close()


