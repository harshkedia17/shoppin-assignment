import logging
import os
from typing import Optional
from bs4 import BeautifulSoup, Tag
from pydantic import HttpUrl

from src.utils.gemini_extractor import GeminiSizeChartExtractor

from .base import BaseExtractor
from ..models.size_chart import Product
from ..utils.selenium_client import SeleniumClient

logger = logging.getLogger(__name__)


class SquahExtractor(BaseExtractor):
    """Extractor for Squah using Selenium for JavaScript rendering."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.selenium_client = SeleniumClient(
            headless=True,
            timeout=30,
            page_load_timeout=30,
            wait_for_element="figure"
        )
        self.gemini_extractor = GeminiSizeChartExtractor(
            api_key=os.environ.get("GEMINI_API_KEY", ""),
            model_name="gemini-2.5-flash"
        )

    async def extract_size_chart(self, product_url: str) -> Optional[Product]:
        try:
            title = await self.extract_title(product_url)
            if not title:
                logger.warning(f"Could not extract title from {product_url}")
                return None

            html = await self.selenium_client.get_rendered_html(product_url)
            soup = BeautifulSoup(html, 'lxml')

            figure = soup.find('figure')
            if figure and isinstance(figure, Tag):
                img = figure.find('img')
                if img and isinstance(img, Tag) and img.get('src'):
                    size_chart = await self.gemini_extractor.extract_table(str(img['src']))

            return Product(
                product_title=title,
                product_url=HttpUrl(product_url),
                size_chart=size_chart
            )

        except Exception as e:
            logger.error(f"Failed to extract from {product_url}: {e}")
            return None
        finally:
            await self.selenium_client.close()

    async def close(self):
        """Clean up resources."""
        await self.selenium_client.close()
