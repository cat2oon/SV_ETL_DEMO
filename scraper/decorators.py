from functools import wraps
from scraper.logger import get_logger
from scraper.tools import inspect_func_params

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

logger = get_logger("-")


def with_user_agent(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, headers={"User-Agent": USER_AGENT}, **kwargs)

    return wrapper


def wrap_log(message=""):
    def logging(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # TODO: 메시지 형식 인자 디폴트 값 처리
            params = inspect_func_params(func, *args, **kwargs)
            msg = message.format(**params)

            logger.debug(f"START {func.__name__} {msg}")
            return_values = func(*args, **kwargs)
            logger.debug(f"FINAL {func.__name__} {msg}")

            return return_values

        return wrapper

    return logging
