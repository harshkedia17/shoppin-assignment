"""
Tests for extractors.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from src.extractors.base import BaseExtractor
from src.extractors.generic_shopify import GenericShopifyExtractor
from src.utils.http_client import HTTPClient
from src.utils.rate_limiter import RateLimiter
from src.models.size_chart import Product, SizeChart


class TestGenericShopifyExtractor:
    """Test cases for GenericShopifyExtractor."""

    @pytest.fixture
    def mock_http_client(self):
        """Create a mock HTTP client."""
        client = Mock(spec=HTTPClient)
        client.get = AsyncMock()
        client.get_json = AsyncMock()
        return client

    @pytest.fixture
    def mock_rate_limiter(self):
        """Create a mock rate limiter."""
        limiter = Mock(spec=RateLimiter)
        limiter.__aenter__ = AsyncMock(return_value=limiter)
        limiter.__aexit__ = AsyncMock(return_value=None)
        return limiter

    @pytest.fixture
    def extractor(self, mock_http_client, mock_rate_limiter):
        """Create an extractor instance."""
        return GenericShopifyExtractor(
            store_url="test.com",
            http_client=mock_http_client,
            rate_limiter=mock_rate_limiter,
            max_products=10
        )

    @pytest.mark.asyncio
    async def test_get_product_urls_via_json(self, extractor):
        """Test getting product URLs via products.json."""
        # Mock products.json response
        extractor.http_client.get_json.return_value = {
            'products': [
                {'handle': 'product-1'},
                {'handle': 'product-2'},
                {'handle': 'product-3'}
            ]
        }

        urls = await extractor.get_product_urls()

        assert len(urls) == 3
        assert 'https://test.com/products/product-1' in urls
        assert 'https://test.com/products/product-2' in urls
        assert 'https://test.com/products/product-3' in urls

    @pytest.mark.asyncio
    async def test_extract_size_chart_from_html(self, extractor):
        """Test extracting size chart from HTML."""
        html = """
        <html>
            <head>
                <title>Test Product</title>
            </head>
            <body>
                <h1>Test Product Name</h1>
                <table class="size-chart">
                    <tr>
                        <th>Size</th>
                        <th>Chest</th>
                    </tr>
                    <tr>
                        <td>S</td>
                        <td>36</td>
                    </tr>
                    <tr>
                        <td>M</td>
                        <td>38</td>
                    </tr>
                </table>
            </body>
        </html>
        """

        extractor.http_client.get.return_value = html

        product = await extractor.extract_size_chart('https://test.com/products/test')

        assert product is not None
        assert product.product_title == "Test Product Name"
        assert product.size_chart is not None
        assert product.size_chart.headers == ['Size', 'Chest']
        assert len(product.size_chart.rows) == 2
        assert product.size_chart.rows[0] == {'Size': 'S', 'Chest': '36'}

    @pytest.mark.asyncio
    async def test_extract_all(self, extractor):
        """Test extracting from all products."""
        # Mock get_product_urls
        with patch.object(extractor, 'get_product_urls', new_callable=AsyncMock) as mock_get_urls:
            mock_get_urls.return_value = [
                'https://test.com/products/product-1',
                'https://test.com/products/product-2'
            ]

            # Mock extract_size_chart
            with patch.object(extractor, 'extract_size_chart', new_callable=AsyncMock) as mock_extract:
                mock_extract.side_effect = [
                    Product(
                        product_title="Product 1",
                        product_url="https://test.com/products/product-1",
                        size_chart=SizeChart(
                            headers=['Size', 'Length'],
                            rows=[{'Size': 'S', 'Length': '25'}]
                        )
                    ),
                    None  # Second product has no size chart
                ]

                result = await extractor.extract_all()

                assert result.store_name == 'test.com'
                # Only one product had a size chart
                assert len(result.products) == 1
                assert result.products[0].product_title == "Product 1"
