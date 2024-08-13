import logging
import aiofiles
import functools

def handle_errors(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            return "An error occurred while processing your request."
    return wrapper

logger = logging.getLogger('UnifiedBot')
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

def log_info(message):
    logger.info(message)

async def write_to_file(filename, data):
    async with aiofiles.open(filename, mode='w') as f:
        await f.write(data)