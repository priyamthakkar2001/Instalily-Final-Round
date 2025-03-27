import os
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional

# Load environment variables from .env file
load_dotenv()

class StoreConfig(BaseModel):
    """Store configuration model"""
    customer_id: str = os.getenv("CUSTOMER_ID", "HPTA")
    branch_code: str = os.getenv("BRANCH_CODE", "BELHARR")
    ship_to_sequence: str = os.getenv("SHIP_TO_SEQUENCE", "1")

class APIConfig(BaseModel):
    """API configuration model"""
    base_url: str = os.getenv("BASE_URL", "https://candidate-onsite-study-srs-712206638513.us-central1.run.app")
    store_config: StoreConfig = StoreConfig()

class OpenAIConfig(BaseModel):
    """OpenAI configuration model"""
    api_key: str = os.getenv("OPENAI_API_KEY", "")
    model: str = "gpt-4o"

class TelegramConfig(BaseModel):
    """Telegram configuration model"""
    bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

class Config(BaseModel):
    """Main configuration model"""
    api: APIConfig = APIConfig()
    openai: OpenAIConfig = OpenAIConfig()
    telegram: TelegramConfig = TelegramConfig()
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

# Create a global config instance
config = Config()

def get_config() -> Config:
    """Get the global configuration instance"""
    return config
