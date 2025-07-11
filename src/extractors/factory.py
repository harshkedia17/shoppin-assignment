"""
Factory for creating store-specific extractors.
"""
import logging
from typing import Dict, Type

from src.extractors.suqah import SuqahExtractor

from .base import BaseExtractor
from .westside import WestsideExtractor
from .littleboxindia import LittleBoxIndiaExtractor
from .freakins import FreakinsExtractor
from ..utils.http_client import HTTPClient
from ..utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class ExtractorFactory:
    """Factory for creating store-specific extractors."""
    EXTRACTORS: Dict[str, Type[BaseExtractor]] = {
        'www.westside.com': WestsideExtractor,
        'www.littleboxindia.com': LittleBoxIndiaExtractor,
        'www.freakins.com': FreakinsExtractor,
        'www.suqah.com': SuqahExtractor,
    }

    @classmethod
    def create_extractor(
        cls,
        store_url: str,
        http_client: HTTPClient,
        rate_limiter: RateLimiter,
        max_products: int = 100,
        concurrent_requests: int = 1
    ) -> BaseExtractor:

        store_domain = store_url.lower().strip('/')
        if store_domain.startswith('http://'):
            store_domain = store_domain[7:]
        elif store_domain.startswith('https://'):
            store_domain = store_domain[8:]
        if not store_domain.startswith('www.'):
            store_domain = 'www.' + store_domain


        extractor_class = cls.EXTRACTORS.get(store_domain)
        if not extractor_class:
            logger.warning(f"No specific extractor found for {store_domain}, using default")
            extractor_class = WestsideExtractor

        logger.info(f"Using {extractor_class.__name__} for {store_domain}")
        return extractor_class(
            store_url=store_domain,
            http_client=http_client,
            rate_limiter=rate_limiter,
            max_products=max_products,
            # concurrent_requests=concurrent_requests
        )
