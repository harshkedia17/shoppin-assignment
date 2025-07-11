import logging
from typing import Optional

from .base import BaseExtractor
from ..models.size_chart import Product
from ..utils.selenium_client import SeleniumClient

logger = logging.getLogger(__name__)


class LittleBoxIndiaExtractor(BaseExtractor):
    """Extractor for LittleBoxIndia using Selenium for JavaScript rendering."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.selenium_client = SeleniumClient(
            headless=True,
            timeout=30,
            page_load_timeout=30,
            wait_for_element="#KiwiSizingChart"  # Wait for KiwiSizing to load
        )

    async def extract_size_chart(self, product_url: str) -> Optional[Product]:
        """Extract size chart from LittleBoxIndia product page."""
        try:
            html = await self.selenium_client.get_rendered_html(product_url)
            return await self.extract_product_data_from_html(html, product_url)

        except Exception as e:
            logger.error(f"Failed to extract from {product_url}: {e}")
            return None
        finally:
            await self.selenium_client.close()

    async def close(self):
        """Clean up resources."""
        await self.selenium_client.close()
