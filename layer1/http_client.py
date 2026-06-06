import logging
import time
from typing import Callable, Optional

import requests

logger = logging.getLogger(__name__)


def default_is_retryable(error: Exception) -> bool:
    if isinstance(error, requests.Timeout):
        return True
    if isinstance(error, requests.ConnectionError):
        return True
    if hasattr(error, "response") and error.response is not None:
        if error.response.status_code == 429:
            return True
        if 500 <= error.response.status_code < 600:
            return True
    return False


def fetch_with_retry(
    url: str,
    timeout: int,
    retry_delay: int = 5,
    max_attempts: int = 2,
    headers: Optional[dict] = None,
    is_retryable: Optional[Callable[[Exception], bool]] = None,
) -> Optional[requests.Response]:
    if is_retryable is None:
        is_retryable = default_is_retryable

    last_error: Optional[Exception] = None

    for attempt in range(1, max_attempts + 1):
        try:
            resp = requests.get(url, timeout=timeout, headers=headers)
            if not resp.ok:
                exc = requests.HTTPError(response=resp)
                if is_retryable(exc) and attempt < max_attempts:
                    logger.warning(
                        "HTTP %d on attempt %d/%d for %s — retrying in %ds",
                        resp.status_code, attempt, max_attempts, url, retry_delay,
                    )
                    time.sleep(retry_delay)
                    continue
                resp.raise_for_status()
            return resp
        except (requests.Timeout, requests.ConnectionError) as e:
            last_error = e
            if attempt < max_attempts:
                logger.warning(
                    "%s on attempt %d/%d for %s — retrying in %ds",
                    type(e).__name__, attempt, max_attempts, url, retry_delay,
                )
                time.sleep(retry_delay)
        except requests.HTTPError as e:
            if is_retryable(e) and attempt < max_attempts:
                logger.warning(
                    "HTTP %d on attempt %d/%d for %s — retrying in %ds",
                    e.response.status_code, attempt, max_attempts, url, retry_delay,
                )
                time.sleep(retry_delay)
                last_error = e
            else:
                logger.error(
                    "Non-retryable HTTP %d for %s",
                    e.response.status_code if e.response is not None else 0, url,
                )
                return None

    if last_error is not None:
        logger.error("All %d attempts failed for %s: %s", max_attempts, url, last_error)
    return None
