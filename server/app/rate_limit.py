import threading
import time

from app.config import RATE_LIMIT_MAX_REQUESTS, RATE_LIMIT_WINDOW_SECONDS

_lock = threading.Lock()
_hits: dict[str, list[float]] = {}


class RateLimitExceeded(Exception):
    pass


def reset() -> None:
    with _lock:
        _hits.clear()


def check_rate_limit(client_id: str) -> None:
    now = time.monotonic()
    window_start = now - RATE_LIMIT_WINDOW_SECONDS
    with _lock:
        recent = [hit for hit in _hits.get(client_id, []) if hit > window_start]
        if len(recent) >= RATE_LIMIT_MAX_REQUESTS:
            _hits[client_id] = recent
            raise RateLimitExceeded(f"Rate limit exceeded for '{client_id}'.")
        recent.append(now)
        _hits[client_id] = recent
