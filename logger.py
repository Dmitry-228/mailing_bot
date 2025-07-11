import logging
import sys
import asyncio
import functools
from logging.handlers import RotatingFileHandler


logger = logging.getLogger('bot_logger')
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# bot.log — всё
file_all = RotatingFileHandler('app/logs/bot.log', maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
file_all.setLevel(logging.DEBUG)
file_all.setFormatter(formatter)

# errors.log — только WARNING 
file_errors = RotatingFileHandler('app/logs/errors.log', maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
file_errors.setLevel(logging.WARNING)
file_errors.setFormatter(formatter)

console = logging.StreamHandler(sys.stdout)
console.setLevel(logging.INFO) 
console.setFormatter(formatter)

logger.addHandler(file_all)
logger.addHandler(file_errors)
logger.addHandler(console)

def log_function(func):
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        logger.debug(f'Вызов {func.__name__} с args={args}, kwargs={kwargs}')
        try:
            result = await func(*args, **kwargs)
            logger.debug(f'{func.__name__} завершена')
            return result
        except Exception:
            logger.exception(f'Ошибка в async-функции {func.__name__}')
            raise

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        logger.debug(f'Вызов {func.__name__} с args={args}, kwargs={kwargs}')
        try:
            result = func(*args, **kwargs)
            logger.debug(f'{func.__name__} завершена')
            return result
        except Exception:
            logger.exception(f'Ошибка в sync-функции {func.__name__}')
            raise

    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
