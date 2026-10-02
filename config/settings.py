"""
Configuration and settings for AI-Powered Multi-Source Event Intelligence System.
Group No. 61 | Rishu Raj | Shaheed Arman Gazi
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings

PROJECT_ROOT = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI-Powered Multi-Source Event Intelligence & Market Impact Analysis"
    GROUP_INFO: str = "Group No. 61 | Rishu Raj | Shaheed Arman Gazi"
    VERSION: str = "1.0.0"
    
    # Base paths
    BASE_DIR: Path = PROJECT_ROOT
    DATA_DIR: Path = PROJECT_ROOT / "data"
    DB_PATH: Path = PROJECT_ROOT / "data" / "event_intelligence.db"
    
    # Ingestion & Preprocessing settings
    DEDUPLICATION_THRESHOLD: float = 0.85
    MIN_ARTICLE_LENGTH: int = 40
    DEFAULT_LOOKBACK_DAYS: int = 30
    
    # Market Analysis settings
    EVENT_PRE_WINDOW_DAYS: int = 5
    EVENT_POST_WINDOW_DAYS: int = 5
    ABNORMAL_VOLUME_THRESHOLD: float = 2.0  # z-score standard deviations
    
    # Knowledge Graph settings
    MAX_GRAPH_HOPS: int = 3
    DEFAULT_CREDIBILITY_WEIGHT: float = 0.70
    
    # API server
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    
    model_config = {"env_file": ".env", "extra": "ignore"}

settings = Settings()
os.makedirs(settings.DATA_DIR, exist_ok=True)

