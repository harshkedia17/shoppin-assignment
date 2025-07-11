"""
Factory for creating store-specific extractors.
"""
import logging
from typing import Dict, Type

from src.extractors.squah import SquahExtractor

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
        'westside.com': WestsideExtractor,
        'littleboxindia.com': LittleBoxIndiaExtractor,
        'freakins.com': FreakinsExtractor,
        'www.squah.com': SquahExtractor,
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

        extractor_class = cls.EXTRACTORS.get(store_domain, WestsideExtractor)

        logger.info(f"Using {extractor_class.__name__} for {store_domain}")

        return extractor_class(
            store_url=store_url,
            http_client=http_client,
            rate_limiter=rate_limiter,
            max_products=max_products,
            # concurrent_requests=concurrent_requests
        )
