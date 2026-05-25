from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/incident_monitor"
    discord_webhook_url: str = "https://discord.com/api/webhooks/1508586657987952811/6-lUmxFzTcME4cC4LEzmOOLcWITVcbfilyJZe3gxAk1a3kiyZ5aUVAg-rN-o_fesCsk-"
    check_interval_seconds: int = 60
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
