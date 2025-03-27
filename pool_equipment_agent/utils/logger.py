import sys
from loguru import logger
from .config import get_config

config = get_config()

# Configure logger
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=config.log_level,
    colorize=True,
)
logger.add(
    "logs/pool_equipment_agent.log",
    rotation="10 MB",
    retention="1 week",
    level=config.log_level,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
)

# Export logger
get_logger = lambda: logger
