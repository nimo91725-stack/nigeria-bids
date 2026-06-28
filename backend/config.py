from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "change-me-in-production"
    # Email (IMAP) for parsing tender alert emails
    imap_host: str = ""
    imap_user: str = ""
    imap_password: str = ""
    imap_folder: str = "INBOX"
    # Alert notifications
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    alert_from_email: str = ""
    # SAM.gov API (free key from api.data.gov)
    samgov_api_key: str = "DEMO_KEY"
    # Google Custom Search (newspaper tender scraping)
    google_search_api_key: str = ""
    google_search_cx: str = ""
    # Google Gemini API (AI relevance scoring)
    gemini_api_key: str = ""
    # SalesPilot bridge
    salespilot_api_url: str = "https://salespilot-api-350631615628.africa-south1.run.app"
    salespilot_email: str = ""
    salespilot_password: str = ""
    salespilot_min_score: int = 70

    class Config:
        env_file = ".env"


settings = Settings()
