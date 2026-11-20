from contextlib import asynccontextmanager
from itertools import count
import json

import aio_pika
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # підключив RabbitMQ і оголосив fanout exchange orders
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    channel = await connection.channel()
    exchange = await channel.declare_exchange(
        "orders",
        aio_pika.ExchangeType.FANOUT,
        durable=True,
    )
    app.state.exchange = exchange
    try:
        yield
    finally:
        await connection.close()


app = FastAPI(title="Замовлення", lifespan=lifespan)

ORDERS: dict[int, dict] = {}
next_id = count(1)


class OrderCreate(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    product: str = Field(min_length=1, max_length=100)
    quantity: int = Field(default=1, ge=1, le=100)


def email_status(order_id: int) -> str:
    return "sent" if (settings.outbox_dir / f"{order_id}.txt").exists() else "pending"


@app.post("/orders", status_code=201)
async def create_order(data: OrderCreate, request: Request):
    order = {"id": next(next_id), **data.model_dump()}
    ORDERS[order["id"]] = order

    # опублікував замовлення в orders із PERSISTENT доставкою
    await request.app.state.exchange.publish(
        aio_pika.Message(
            body=json.dumps(order).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        ),
        routing_key="",
    )
    return order


@app.get("/orders")
async def list_orders():
    return [{**order, "email_status": email_status(order["id"])} for order in ORDERS.values()]


@app.get("/orders/{order_id}")
async def get_order(order_id: int):
    order = ORDERS.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Замовлення не знайдено")
    return {**order, "email_status": email_status(order_id)}
