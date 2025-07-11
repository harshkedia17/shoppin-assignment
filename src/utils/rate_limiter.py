from asyncio_throttle.throttler import Throttler


class RateLimiter:
    """Rate limiter for controlling request frequency."""

    def __init__(self, rate_limit: float = 1.0):
        self.rate_limit = rate_limit
        self.throttler = Throttler(rate_limit=int(1/rate_limit) if rate_limit > 0 else float('inf'))  # type: ignore

    async def acquire(self):
        await self.throttler.acquire()

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
