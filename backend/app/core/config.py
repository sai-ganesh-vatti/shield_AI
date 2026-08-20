from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./pharma_twin.db")
    database_url_sync: str = os.getenv("DATABASE_URL_SYNC", "sqlite:///./pharma_twin.db")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    mapbox_access_token: str = os.getenv("MAPBOX_ACCESS_TOKEN", "")
    simulation_tick_interval: float = float(os.getenv("SIMULATION_TICK_INTERVAL", "1.0"))
    health_storm_duration: int = int(os.getenv("HEALTH_STORM_DURATION", "300"))
    max_trucks: int = int(os.getenv("MAX_TRUCKS", "50"))
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()