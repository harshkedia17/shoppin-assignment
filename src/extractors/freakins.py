import logging
import os
import traceback
from typing import Optional
from bs4 import BeautifulSoup
from pydantic import HttpUrl

from src.utils.gemini_extractor import GeminiSizeChartExtractor

from .base import BaseExtractor
from ..models.size_chart import Product, StoreResult
from ..utils.selenium_client import SeleniumClient

logger = logging.getLogger(__name__)


class FreakinsExtractor(BaseExtractor):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.selenium_client = SeleniumClient(
            headless=True,
            timeout=30,
            page_load_timeout=30,
            wait_for_element=".newsletter-modal"
        )
        self.gemini_extractor = GeminiSizeChartExtractor(
            api_key=os.environ.get("GEMINI_API_KEY", ""),
            model_name="gemini-2.0-flash-exp"
        )

    async def extract_size_chart(self, product_url: str) -> Optional[Product]:
        try:
            title = await self.extract_title(product_url)
            if not title:
                logger.warning(f"Could not extract title from {product_url}")
                return None

            html = await self.selenium_client.get_rendered_html(product_url)
            soup = BeautifulSoup(html, 'lxml')
            div = soup.find('div', class_='newsletter-modal')
            size_chart = None

            if div:
                img = div.find('img')
                if img and img.get('src'):
                    size_chart = await self.gemini_extractor.extract_table(str(img['src']))

            if size_chart:
                return Product(
                    product_title=title,
                    product_url=HttpUrl(product_url),
                    size_chart=size_chart
                )
            else:
                logger.warning(f"No size chart found for {title}")
                return None

        except Exception as e:
            logger.error(f"Failed to extract from {product_url}: {e}")
            logger.error(traceback.format_exc())
            return None

    async def extract_all(self) -> StoreResult:
        try:
            result = await super().extract_all()
            return result
        finally:
            await self.close()

    async def close(self):
        """Clean up resources."""
        await self.selenium_client.close()
