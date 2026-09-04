from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://cortex:cortex@localhost:5432/cortex"
    redis_url: str = "redis://localhost:6379/0"

    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    ollama_embedding_model: str = "nomic-embed-text"

    # dev-only default - every real deployment must override this
    jwt_secret_key: str = "dev-secret-do-not-use-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    # the refresh-token cookie's Secure flag - only safe to leave False over
    # plain HTTP for local dev; a real deployment behind HTTPS must set this
    cookie_secure: bool = False


settings = Settings()
