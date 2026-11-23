from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    environment: str = "development"
    secret_key: str = "change-me"
    database_url: str = "sqlite:///./forexpilot.db"
    # Where the API reaches the engine's read-only status server (same DB is the trading contract).
    engine_api_url: str = "http://127.0.0.1:8001"
    cors_origins: str = "http://localhost:3000"
    allow_registration: bool = False
    token_minutes: int = 60 * 12
    cookie_secure: bool = False
    cookie_samesite: str = "lax"


settings = Settings()
