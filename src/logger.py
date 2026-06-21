from functools import lru_cache
import sys
from loguru import logger

logger.remove()
logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>")

@lru_cache()
def get_logger(name: str):
    return logger.bind(name=name)