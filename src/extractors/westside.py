import logging
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from .base import BaseExtractor
from ..models.size_chart import Product

logger = logging.getLogger(__name__)


class WestsideExtractor(BaseExtractor):

    async def extract_size_chart(self, product_url: str) -> Optional[Product]:

        try:
            async with self.rate_limiter:
                html = await self.http_client.get(product_url)

            return await self.extract_product_data_from_html(html, product_url)

        except Exception as e:
            logger.error(f"Failed to extract from {product_url}: {e}")
            return None
