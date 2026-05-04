from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    anthropic_api_key: str
    watch_folder: str = "./data/watch"
    database_url: str = "sqlite+aiosqlite:///./data/summaries.db"
    log_level: str = "INFO"

    # FastAPI
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = ["http://localhost:5173"]

    # Anthropic
    model: str = "claude-sonnet-4-5"
    max_tokens: int = 2048


settings = Settings()  # type: ignore[call-arg]
