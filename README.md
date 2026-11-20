# Замовлення

Маленький FastAPI-застосунок для практичної роботи з RabbitMQ.

Запуск: `uvicorn main:app --reload`, Swagger на http://127.0.0.1:8000/docs.

- `POST /orders` створює замовлення і надсилає лист-підтвердження. Лист іде 3 секунди, і весь цей час клієнт чекає.
- `GET /orders`, `GET /orders/{id}` показують замовлення і `email_status`: `pending` або `sent`.
- Надіслані листи з'являються в папці `outbox/`.
- `emails.py` імітує поштовий сервер, змінювати його не потрібно. Адреси на `.invalid` (наприклад `bob@mail.invalid`)
  імітують збій пошти: `send_confirmation` кидає `ConnectionError`.
