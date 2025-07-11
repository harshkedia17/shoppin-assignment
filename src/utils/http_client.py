
import asyncio
import logging
from typing import Optional, Dict, Any
import aiohttp
from aiohttp import ClientSession, ClientTimeout
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)


class HTTPClient:

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        user_agent: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        self.timeout = ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.ua = UserAgent()
        self.user_agent = user_agent or self.ua.random
        self.headers = headers or {}
        self.session: Optional[ClientSession] = None

    async def __aenter__(self):
        self.session = ClientSession(
            timeout=self.timeout,
            headers={
                'User-Agent': self.user_agent,
                **self.headers
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(
            (aiohttp.ClientError, asyncio.TimeoutError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def get(self, url: str, **kwargs) -> str:

        if not self.session:
            raise RuntimeError("HTTPClient must be used as a context manager")

        async with self.session.get(url, **kwargs) as response:
            response.raise_for_status()
            return await response.text()

    async def get_json(self, url: str, **kwargs) -> Dict[str, Any]:
        if not self.session:
            raise RuntimeError("HTTPClient must be used as a context manager")

        async with self.session.get(url, **kwargs) as response:
            response.raise_for_status()
            return await response.json()
