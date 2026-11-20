import asyncio
import json

import aio_pika

from config import settings
from emails import send_confirmation


async def handle(message: aio_pika.abc.AbstractIncomingMessage) -> None:
    # налаштував requeue при перериванні та захист від повторного циклу помилок
    async with message.process(requeue=True, reject_on_redelivered=True):
        order = json.loads(message.body)
        print("sending", order["id"])
        await send_confirmation(order)
        print("sent", order["id"])


async def main() -> None:
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            "orders",
            aio_pika.ExchangeType.FANOUT,
            durable=True,
        )
        queue = await channel.declare_queue("emails", durable=True)
        await queue.bind(exchange)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                try:
                    await handle(message)
                except Exception as e:
                    print("error:", e)


if __name__ == "__main__":
    asyncio.run(main())
