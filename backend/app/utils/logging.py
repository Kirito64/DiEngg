from loguru import logger
import sys
from app.config import get_settings

settings = get_settings()

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.LOG_LEVEL
)
logger.add(
    "logs/diengg.log",
    rotation="1 day",
    retention="7 days",
    level=settings.LOG_LEVEL
) 