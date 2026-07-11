from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./jobs.db"
    # Which scraper backend to use: "apify" (default) or "brightdata".
    # Flip SCRAPER_PROVIDER in .env to switch — no code changes needed.
    scraper_provider: str = "apify"
    apify_api_token: str = ""
    # Bright Data (only used when scraper_provider == "brightdata")
    brightdata_api_token: str = ""
    brightdata_dataset_id: str = "gd_lpfll7v5hcqtkxl6l"
    # Country hint sent to Bright Data discovery (LinkedIn geo). Default matches prior setup.
    brightdata_country: str = "SE"
    llm_api_key: str = ""
    llm_provider: str = "openrouter"
    llm_model: str = "deepseek/deepseek-v4-flash"
    # Reasoning effort for RELEVANCE SCORING only ("" = off, "high", "xhigh"=max).
    # Cover letters and chat are unaffected.
    llm_reasoning_effort: str = ""
    secret_key: str = "change-me-in-production"

    class Config:
        env_file = ".env"


settings = Settings()
