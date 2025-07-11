import asyncio
import time
from typing import Optional
from asyncio_throttle.throttler import Throttler


class RateLimiter:
    """Rate limiter for controlling request frequency."""

    def __init__(self, rate_limit: float = 1.0, burst: int = 1):

        self.rate_limit = rate_limit
        self.burst = burst
        self.throttler = Throttler(rate_limit=int(1/rate_limit) if rate_limit > 0 else float('inf'))  # type: ignore
        self._last_request_time = 0
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            current_time = time.time()
            time_since_last = current_time - self._last_request_time

            if time_since_last < self.rate_limit:
                await asyncio.sleep(self.rate_limit - time_since_last)

            self._last_request_time = time.time()

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class DynamicRateLimiter(RateLimiter):

    def __init__(self, initial_rate: float = 1.0, min_rate: float = 0.5, max_rate: float = 5.0):
        super().__init__(initial_rate)
        self.min_rate = min_rate
        self.max_rate = max_rate
        self.error_count = 0
        self.success_count = 0

    def adjust_rate(self, success: bool, response_time: Optional[float] = None):
        if success:
            self.success_count += 1
            self.error_count = max(0, self.error_count - 1)

            if self.success_count > 10 and self.rate_limit > self.min_rate:
                self.rate_limit = max(self.min_rate, self.rate_limit * 0.9)
        else:
            self.error_count += 1
            self.success_count = 0

            if self.error_count > 2:
                self.rate_limit = min(self.max_rate, self.rate_limit * 1.5)
