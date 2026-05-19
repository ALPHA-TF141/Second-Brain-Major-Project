from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Second Brain Backend"
    app_env: str = "development"
    database_url: str = "sqlite:///./data/second_brain.db"
    jwt_secret_key: str = "change-this-dev-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    demo_username: str = "demo"
    demo_password: str = "secondbrain"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    rag_context_limit: int = 8

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origin_list(self):
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
