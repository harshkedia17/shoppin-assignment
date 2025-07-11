import asyncio
import json
import logging
from datetime import datetime, UTC
from typing import List
from pathlib import Path

from .models.size_chart import ExtractionConfig, StoreResult
from .extractors.factory import ExtractorFactory
from .utils.http_client import HTTPClient
from .utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class SizeChartExtractorService:

    def __init__(self, config: ExtractionConfig):
        self.config = config or ExtractionConfig()

    async def extract_store(self, store_url: str) -> StoreResult:
        logger.info(f"Starting extraction for {store_url}")

        rate_limiter = RateLimiter(
            rate_limit=self.config.rate_limit_delay,
            burst=self.config.concurrent_requests
        )

        async with HTTPClient(
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
            user_agent=self.config.user_agent
        ) as http_client:
            extractor = ExtractorFactory.create_extractor(
                store_url=store_url,
                http_client=http_client,
                rate_limiter=rate_limiter,
                max_products=self.config.max_products_per_store
            )

            result = await extractor.extract_all()
            result.extraction_date = datetime.now(UTC).isoformat()

            logger.info(
                f"Completed extraction for {store_url}: "
                f"{len(result.products)} products with size charts found"
            )

            return result

    async def extract_stores(self, store_urls: List[str]) -> List[StoreResult]:
        semaphore = asyncio.Semaphore(self.config.concurrent_requests)

        async def extract_with_semaphore(store_url: str) -> StoreResult:
            async with semaphore:
                try:
                    return await self.extract_store(store_url)
                except Exception as e:
                    logger.error(f"Failed to extract {store_url}: {e}")
                    return StoreResult(
                        store_name=store_url,
                        products=[],
                        errors=[f"Extraction failed: {str(e)}"],
                        extraction_date=datetime.now(UTC).isoformat()
                    )

        tasks = [extract_with_semaphore(url) for url in store_urls]
        results = await asyncio.gather(*tasks)

        return results

    def save_results(self, results: List[StoreResult], output_path: str = "output.json"):
        output_data = []
        for result in results:
            store_data = {
                "store_name": result.store_name,
                "extraction_date": result.extraction_date,
                "products": []
            }

            for product in result.products:
                if product.size_chart:
                    product_data = {
                        "product_title": product.product_title,
                        "product_url": str(product.product_url),
                        "size_chart": {
                            "headers": product.size_chart.headers,
                            "rows": product.size_chart.rows
                        }
                    }
                    store_data["products"].append(product_data)

            if result.errors:
                store_data["errors"] = result.errors

            output_data.append(store_data)

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Results saved to {output_file}")

    async def run(self, store_urls: List[str], output_path: str = "output.json") -> List[StoreResult]:
        results = await self.extract_stores(store_urls)  # type: ignore # TODO: fix this

        self.save_results(results, output_path)

        total_products = sum(len(r.products) for r in results)
        total_errors = sum(len(r.errors) for r in results)

        logger.info(
            f"Extraction complete: {len(results)} stores, "
            f"{total_products} products with size charts, "
            f"{total_errors} errors"
        )

        return results
