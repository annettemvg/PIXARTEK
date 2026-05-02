from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "PIXARTEK API"
    debug: bool = False

    # MQTT
    mqtt_host: str = "localhost"
    mqtt_port: int = 1883
    mqtt_keepalive: int = 60

    # Database
    db_url: str = "sqlite+aiosqlite:///./pixartek.db"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    class Config:
        env_file = ".env"


settings = Settings()
