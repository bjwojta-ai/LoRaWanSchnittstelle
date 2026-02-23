from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # The Things Network / LoRaWAN Network Server
    ttn_api_key: str = ""
    ttn_app_id: str = ""
    ttn_tenant_id: str = "ttn"
    ttn_base_url: str = "https://eu1.cloud.thethings.network"

    # MQTT
    mqtt_host: str = "eu1.cloud.thethings.network"
    mqtt_port: int = 8883
    mqtt_username: str = ""
    mqtt_password: str = ""
    mqtt_use_tls: bool = True

    # API server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "info"


settings = Settings()
