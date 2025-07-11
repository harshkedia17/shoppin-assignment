from datetime import datetime, UTC
import re
import json
import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from pydantic import HttpUrl

from ..models.size_chart import Product, SizeChart, StoreResult
from ..utils.http_client import HTTPClient
from ..utils.parser import SizeChartParser
from ..utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class BaseExtractor(ABC):

    def __init__(
        self,
        store_url: str,
        http_client: HTTPClient,
        rate_limiter: RateLimiter,
        max_products: int = 100
    ):

        self.store_url = store_url.strip('/')
        if not self.store_url.startswith('http'):
            self.store_url = f'https://{self.store_url}'

        self.http_client = http_client
        self.rate_limiter = rate_limiter
        self.max_products = max_products
        self.parser = SizeChartParser()


    @abstractmethod
    async def extract_size_chart(self, product_url: str) -> Optional[Product]:
        pass


    async def extract_title(self, product_url: str) -> Optional[str]:
        json_url = f'{product_url}.json'
        async with self.rate_limiter:
            data = await self.http_client.get_json(json_url)

        return data.get('product', {}).get('title')


    async def get_collections(self) -> List[str]:
        collections = []
        try:
            url = urljoin(self.store_url, '/collections.json')
            async with self.rate_limiter:
                data = await self.http_client.get_json(url)
                if 'collections' in data:
                    for collection in data['collections']:
                        handle = collection.get('handle')
                        if handle:
                            collections.append(urljoin(self.store_url,f'/collections/{handle}'))
        except Exception as e:
            logger.debug(f"Failed to get collections from /collections.json: {e}")


        return collections  

    async def get_shopify_products_json(self) -> List[Dict[str, Any]]:
        products = []
        page = 1
        
        while len(products) < self.max_products:
            try:
                url = f"{self.store_url}/products.json?page={page}&limit=250"
                async with self.rate_limiter:
                    data = await self.http_client.get_json(url)
                
                page_products = data.get('products', [])
                
                if not page_products:
                    break
                
                for product in page_products:
                    if len(products) < self.max_products:
                        products.append(product)
                    else:
                        break
                
                if len(page_products) < 250:
                    break
                
                page += 1
                
            except Exception as e:
                logger.warning(f"Failed to get products.json page {page}: {e}")
                break
        
        logger.info(f"Retrieved {len(products)} products from products.json API")
        return products


    async def get_product_urls(self) -> List[str]:
        product_urls = []

        try:
            products = await self.get_shopify_products_json()
            for product in products:
                handle = product.get('handle')
                if handle:
                    url = urljoin(self.store_url, f'/products/{handle}')
                    product_urls.append(url)

            if product_urls:
                logger.info(f"Found {len(product_urls)} products via products.json")
                return product_urls
        except Exception as e:
            logger.warning(f"Failed to get products via JSON API: {e}")

        try:
            collections = await self.get_collections()
            logger.info(f"Found {len(collections)} collections")

            for collection_url in collections[:10]:
                try:
                    collection_products = await self._get_products_from_collection(collection_url)
                    product_urls.extend(collection_products)

                    if len(product_urls) >= self.max_products:
                        break

                except Exception as e:
                    logger.warning(
                        f"Failed to get products from {collection_url}: {e}")

        except Exception as e:
            logger.warning(f"Failed to get collections: {e}")

        if not product_urls:
            try:
                sitemap_urls = await self._get_products_from_sitemap()
                product_urls.extend(sitemap_urls)
            except Exception as e:
                logger.warning(f"Failed to get products from sitemap: {e}")

        product_urls = list(dict.fromkeys(product_urls))

        return product_urls[:self.max_products]

    async def _get_products_from_collection(self, collection_url: str) -> List[str]:
        products = []

        try:
            json_url = f"{collection_url}/products.json"
            async with self.rate_limiter:
                data = await self.http_client.get_json(json_url)

            for product in data.get('products', []):
                handle = product.get('handle')
                if handle:
                    url = urljoin(self.store_url, f'/products/{handle}')
                    products.append(url)

        except Exception as e:
            logger.debug(f"Failed to get products from {collection_url}: {e}")
            return []

        return products

    async def _get_products_from_sitemap(self) -> List[str]:    
        products = []
        sitemap_urls = []
        parent_xml = urljoin(self.store_url, '/sitemap.xml')
        async with self.rate_limiter:
            xml = await self.http_client.get(parent_xml)
        soup = BeautifulSoup(xml, 'xml')

        for loc in soup.find_all('loc'):
            url  = loc.get_text()
            if '.xml' in url:
                sitemap_urls.append(url)
        

        try:
            for sitemap_url in sitemap_urls:
                async with self.rate_limiter:
                    xml = await self.http_client.get(sitemap_url)
                soup = BeautifulSoup(xml, 'xml')

                for loc in soup.find_all('loc'):
                    url = loc.get_text()
                    if '/products/' in url:
                        products.append(url)

        except Exception as e:
            logger.debug(f"Failed to get sitemap: {e}")

        return products

    async def extract_all(self) -> StoreResult:
        products = []
        errors = []

        try:
            logger.info(f"Extracting {self.max_products} products from {self.store_url}")
            product_urls = await self.get_product_urls()
            logger.info(f"Found {len(product_urls)} products for {self.store_url}")

            for i, url in enumerate(product_urls):
                try:
                    async with self.rate_limiter:
                        logger.debug(f"Extracting {i+1}/{len(product_urls)}: {url}")
                        product = await self.extract_size_chart(url)
                        if product and product.size_chart:
                            products.append(product)
                except Exception as e:
                    error_msg = f"Error extracting {url}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)

        except Exception as e:
            error_msg = f"Error getting product URLs: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)

        return StoreResult(
            store_name=urlparse(self.store_url).netloc,
            products=products,
            errors=errors,
            extraction_date=datetime.now(UTC).isoformat()
        )

    async def extract_product_data_from_html(self, html: str, url: str) -> Optional[Product]:

        soup = BeautifulSoup(html, 'lxml')

        title = await self.extract_title(url)

        if not title:
            logger.warning(f"Could not extract title from {url}")
            return None

        potential_charts = self.parser.find_size_charts(soup)

        if potential_charts:
            table, confidence = potential_charts[0]
            headers, rows = self.parser.extract_table_data(table)

            if headers and rows:
                logger.info(
                    f"Found size chart for {title} (confidence: {confidence:.2f})")
                return Product(
                    product_title=title,
                    product_url=HttpUrl(url),
                    size_chart=SizeChart(headers=headers, rows=rows)
                )
        else:
            logger.warning(f"Could not find size chart for {title} or it doesnt exist")

        return None
