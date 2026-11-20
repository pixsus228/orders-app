from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    rabbitmq_url: str = "amqp://guest:guest@localhost/"
    outbox_dir: Path = Path("outbox")  # сюди «поштовий сервер» кладе надіслані листи
    email_seconds: float = 3  # скільки триває надсилання одного листа


settings = Settings()
