"""Small helpers for retrying transient network failures."""

import random
import time
from typing import Optional

# HTTP statuses worth retrying (rate limiting and transient server errors).
RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})
DEFAULT_ATTEMPTS = 3
MAX_DELAY_SECONDS = 10.0


def sleep(seconds: float) -> None:
    """Indirection so tests can disable real waiting."""
    time.sleep(seconds)


def backoff_delay(attempt: int, retry_after: Optional[str] = None) -> float:
    """Exponential backoff with jitter; honours a numeric Retry-After header."""
    if retry_after:
        try:
            return min(float(retry_after), MAX_DELAY_SECONDS)
        except ValueError:
            pass
    return min(0.5 * (2**attempt) + random.uniform(0, 0.25), MAX_DELAY_SECONDS)
