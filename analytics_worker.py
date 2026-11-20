import asyncio
import json
from pathlib import Path

import aio_pika

from config import settings

STATS_FILE = Path("stats.json")


def load_stats(stats_path: Path) -> dict:
    if not stats_path.exists():
        return {"orders": 0, "items": 0, "products": {}}
    return json.loads(stats_path.read_text(encoding="utf-8"))


def save_stats(stats_path: Path, stats: dict) -> None:
    stats_path.write_text(
        json.dumps(stats, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def apply_order(stats: dict, order: dict) -> dict:
    # оновив лічильники замовлень, одиниць і товарів
    product = order["product"]
    stats["orders"] += 1
    stats["items"] += order["quantity"]
    stats["products"][product] = stats["products"].get(product, 0) + 1
    return stats


async def handle(message: aio_pika.abc.AbstractIncomingMessage) -> None:
    async with message.process(requeue=True, reject_on_redelivered=True):
        order = json.loads(message.body)
        stats = load_stats(STATS_FILE)
        updated = apply_order(stats, order)
        save_stats(STATS_FILE, updated)
        print("analytics updated for order", order["id"])


async def main() -> None:
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            "orders",
            aio_pika.ExchangeType.FANOUT,
            durable=True,
        )
        queue = await channel.declare_queue("analytics", durable=True)
        await queue.bind(exchange)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                try:
                    await handle(message)
                except Exception as e:
                    print("error:", e)


if __name__ == "__main__":
    asyncio.run(main())
