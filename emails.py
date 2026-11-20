"""Імітація поштового сервера. Цей файл змінювати не потрібно."""

import asyncio
from pathlib import Path

from config import settings


async def send_confirmation(order: dict) -> Path:
    """Надсилає лист «Замовлення прийнято». Повільно, як справжня пошта."""
    await asyncio.sleep(settings.email_seconds)
    if order["email"].endswith(".invalid"):
        raise ConnectionError(f"Поштовий сервер не прийняв лист для {order['email']}")

    settings.outbox_dir.mkdir(exist_ok=True)
    path = settings.outbox_dir / f"{order['id']}.txt"
    path.write_text(
        f"Кому: {order['email']}\n"
        f"Тема: Замовлення №{order['id']} прийнято\n\n"
        f"Ви замовили: {order['product']} × {order['quantity']}\n",
        encoding="utf-8",
    )
    return path
