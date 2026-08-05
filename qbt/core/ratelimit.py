"""Thread-safe token bucket rate limiter (WS-A).

Used by WS-B providers to respect per-provider rate limits (e.g. Finam's
200/min) from multiple threads (the API's ThreadPoolExecutor job workers may
call the same provider concurrently).
"""
from __future__ import annotations

import functools
import threading
import time
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")


class TokenBucket:
    """Classic token bucket: refills at `rate_per_min`, holds up to `burst` tokens."""

    def __init__(self, rate_per_min: float, burst: float | None = None):
        if rate_per_min <= 0:
            raise ValueError("rate_per_min must be > 0")
        self.rate_per_min = float(rate_per_min)
        self._rate_per_sec = self.rate_per_min / 60.0
        self.capacity = float(burst) if burst is not None else self.rate_per_min
        if self.capacity <= 0:
            raise ValueError("burst must be > 0")
        self._tokens = self.capacity
        self._lock = threading.Lock()
        self._last = time.monotonic()

    def _refill_locked(self) -> None:
        now = time.monotonic()
        elapsed = max(0.0, now - self._last)
        self._last = now
        self._tokens = min(self.capacity, self._tokens + elapsed * self._rate_per_sec)

    def acquire(self, tokens: float = 1.0, block: bool = True) -> bool:
        """Take `tokens` from the bucket. If `block`, sleep until available.

        Returns True if tokens were taken, False if `block=False` and there
        weren't enough tokens available immediately.
        """
        if tokens <= 0:
            raise ValueError("tokens must be > 0")
        while True:
            with self._lock:
                self._refill_locked()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return True
                deficit = tokens - self._tokens
                wait_s = deficit / self._rate_per_sec
            if not block:
                return False
            time.sleep(wait_s)

    def available(self) -> float:
        with self._lock:
            self._refill_locked()
            return self._tokens


def rate_limited(bucket: TokenBucket) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator: block on `bucket.acquire()` before each call."""

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            bucket.acquire(block=True)
            return fn(*args, **kwargs)

        return wrapper

    return decorator


__all__ = ["TokenBucket", "rate_limited"]
