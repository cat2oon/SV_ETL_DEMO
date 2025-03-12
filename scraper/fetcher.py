import requests

from scraper.logger import get_logger
from scraper.decorators import with_user_agent

logger = get_logger("fetcher")


@with_user_agent
def fetch_page(url, headers=None) -> str | None:
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        logger.debug(f"fetch 성공: {url}")
        return response.text
    except Exception as e:
        logger.exception(f"fetch 예외: {e}")
        return None
