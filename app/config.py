from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./jobs.db"
    apify_api_token: str = ""
    llm_api_key: str = ""
    llm_provider: str = "openrouter"
    llm_model: str = "deepseek/deepseek-v4-flash"
    secret_key: str = "change-me-in-production"

    class Config:
        env_file = ".env"


settings = Settings()
