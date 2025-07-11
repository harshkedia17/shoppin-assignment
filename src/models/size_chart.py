"""
Data models for size chart extraction.
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, HttpUrl




class SizeChart(BaseModel):
    """Represents a complete size chart with headers and rows."""
    headers: List[str] = Field(...,description="Column headers for the size chart")
    rows: List[Dict[str, str]] = Field(..., description="Each row as an object with column headers as keys")


class Product(BaseModel):
    """Represents a product with its size chart."""
    product_title: str = Field(..., description="Product name/title")
    product_url: HttpUrl = Field(..., description="Product page URL")
    size_chart: Optional[SizeChart] = Field(None, description="Product size chart if available")


class StoreResult(BaseModel):
    """Represents extraction results for a single store."""
    store_name: str = Field(..., description="Store domain name")
    products: List[Product] = Field(default_factory=list, description="Products with size charts")
    extraction_date: Optional[str] = Field(None, description="Date of extraction")
    errors: List[str] = Field(default_factory=list,description="Any errors encountered")


class ExtractionConfig(BaseModel):
    """Configuration for extraction process."""
    max_products_per_store: int = Field(default=100, description="Maximum products to extract per store")
    rate_limit_delay: float = Field(default=1.0, description="Delay between requests in seconds")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    concurrent_requests: int = Field(default=5, description="Maximum concurrent requests")
    max_retries: int = Field(default=1, description="Maximum retry attempts")
    user_agent: Optional[str] = Field(default=None, description="User agent string")


class KeyValuePair(BaseModel):
    """Represents a single key-value pair in a size chart row."""
    key: str = Field(..., description="The column header (e.g., 'Size', 'Bust').")
    value: str = Field(..., description="The corresponding value for the header.")

class SizeChartRow(BaseModel):
    """Represents a single row in the size chart as a list of key-value pairs."""
    columns: List[KeyValuePair] = Field(..., description="A list of key-value pairs representing the columns in this row.")

class SizeChartGemini(BaseModel):
    """Represents a complete size chart with headers and rows."""
    headers: List[str] = Field(..., description="Column headers for the size chart")
    rows: List[SizeChartRow] = Field(..., description="Each row as a list of key-value pairs.")

class GeminiSizeChartExtractionResult(BaseModel):
    """Pydantic model for Gemini size chart extraction result."""
    size_chart: Optional[SizeChartGemini] = Field(
        None,
        description="Extracted size chart data"
    )
    confidence: float = Field(
        ...,
        ge=0,
        le=1,
        description="Confidence score of the extraction (0-1)"
    )
    has_size_chart: bool = Field(
        ...,
        description="Whether a size chart was found in the image"
    )