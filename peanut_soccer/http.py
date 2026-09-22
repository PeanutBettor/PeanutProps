"""Polite HTTP: rate limiting, retries with backoff, and a log line for every fetch."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Callable, Optional

import requests

from . import config

log = logging.getLogger("peanut_soccer.http")


class RateLimiter:
    """Blocks so that consecutive calls to wait() are at least `min_interval` seconds apart.

    `clock` and `sleep` are injectable so the limiter can be tested without real waiting.
    """

    def __init__(
        self,
        min_interval: float = config.MIN_REQUEST_INTERVAL_S,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ):
        if min_interval < 0:
            raise ValueError("min_interval must be >= 0")
        self.min_interval = min_interval
        self._clock = clock
        self._sleep = sleep
        self._last: Optional[float] = None

    def wait(self) -> float:
        """Sleep as needed; return the number of seconds slept."""
        now = self._clock()
        slept = 0.0
        if self._last is not None:
            remaining = self.min_interval - (now - self._last)
            if remaining > 0:
                self._sleep(remaining)
                slept = remaining
        self._last = self._clock()
        return slept


class FetchError(Exception):
    def __init__(self, url: str, status: Optional[int], message: str):
        super().__init__(f"{url}: {status} {message}")
        self.url = url
        self.status = status
        self.message = message


@dataclass
class FetchResult:
    url: str
    status: int
    content: bytes


# Status codes worth retrying. 403/404 are not retried: they are blocks or missing pages,
# and hammering them is impolite.
RETRYABLE = {429, 500, 502, 503, 504}


class HttpClient:
    """One client per source, so each source gets its own rate limiter."""

    def __init__(
        self,
        source: str,
        headers: Optional[dict] = None,
        limiter: Optional[RateLimiter] = None,
        max_retries: int = config.MAX_RETRIES,
        backoff_base: float = config.BACKOFF_BASE_S,
        on_fetch: Optional[Callable[[str, str, str, Optional[str]], None]] = None,
        session: Optional[requests.Session] = None,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self.source = source
        self.limiter = limiter or RateLimiter()
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.on_fetch = on_fetch  # callback(source, url, status, error) -> fetch_log row
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": config.USER_AGENT, "Accept": "application/json"})
        if headers:
            self.session.headers.update(headers)
        self._sleep = sleep

    def _record(self, url: str, status: str, error: Optional[str]) -> None:
        if self.on_fetch:
            self.on_fetch(self.source, url, status, error)

    def get(self, url: str, params: Optional[dict] = None, timeout: float = 30.0) -> FetchResult:
        last_err: Optional[FetchError] = None
        for attempt in range(1, self.max_retries + 2):
            self.limiter.wait()
            t0 = time.monotonic()
            try:
                resp = self.session.get(url, params=params, timeout=timeout)
            except requests.RequestException as exc:
                full = requests.Request("GET", url, params=params).prepare().url
                log.warning("FETCH %s %s attempt=%d NETWORK-ERROR %s", self.source, full, attempt, exc)
                self._record(full, "network_error", str(exc)[:500])
                last_err = FetchError(full, None, str(exc))
            else:
                ms = int((time.monotonic() - t0) * 1000)
                log.info(
                    "FETCH %s %s attempt=%d status=%d bytes=%d ms=%d",
                    self.source, resp.url, attempt, resp.status_code, len(resp.content), ms,
                )
                if resp.status_code == 200:
                    self._record(resp.url, "200", None)
                    return FetchResult(resp.url, 200, resp.content)
                err = resp.text[:300]
                self._record(resp.url, str(resp.status_code), err)
                last_err = FetchError(resp.url, resp.status_code, err)
                if resp.status_code not in RETRYABLE:
                    raise last_err
            if attempt <= self.max_retries:
                delay = self.backoff_base * (2 ** (attempt - 1))
                log.info("RETRY %s in %.0fs", self.source, delay)
                self._sleep(delay)
        assert last_err is not None
        raise last_err
