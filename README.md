# Shopify Size Chart Extractor

A robust, scalable service for extracting size chart information from Shopify stores. Built with extensibility and efficiency in mind, this tool can handle multiple stores concurrently while respecting rate limits and handling errors gracefully.

## Features

- **Multi-Store Support**: Extract size charts from multiple Shopify stores concurrently
- **Intelligent Extraction**: Uses multiple strategies to find and extract size charts
- **Rate Limiting**: Dynamic rate limiting to avoid being blocked
- **Error Handling**: Comprehensive error handling with retry logic
- **Extensible Architecture**: Easy to add store-specific extractors
- **Beautiful CLI**: Rich terminal interface with progress indicators
- **Structured Output**: Clean JSON output following the specified format

## Requirements

- Python 3.9 or higher
- pip (Python package installer)

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd assignment
```

2. Create a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -e .
```

For development dependencies:

```bash
pip install -e ".[dev]"
```

## Quick Start

Extract size charts from the required stores:

```bash
python main.py westside.com freakins.com littleboxindia.com suqah.com
```

## Usage

### Basic Usage

Extract from specific stores:

```bash
python main.py westside.com freakins.com
```

### Advanced Options

```bash
# Specify output file
python main.py westside.com --output results.json

# Limit products per store
python main.py westside.com --max-products 50

# Adjust rate limiting
python main.py westside.com --rate-limit 2.0

# Read stores from file
python main.py -f stores.txt

# Enable debug logging
python main.py westside.com --debug

# Adjust concurrency
python main.py westside.com freakins.com --concurrent 3
```

### Command Line Options

- `stores`: Store URLs to extract (e.g., westside.com)
- `-f, --file`: File containing store URLs (one per line)
- `-o, --output`: Output JSON file (default: output.json)
- `--max-products`: Maximum products per store (default: 100)
- `--rate-limit`: Seconds between requests (default: 1.0)
- `--timeout`: Request timeout in seconds (default: 30)
- `--concurrent`: Maximum concurrent requests (default: 5)
- `--debug`: Enable debug logging

## Output Format

The service outputs a JSON file with the following structure:

```json
[
  {
    "store_name": "westside.com",
    "extraction_date": "2024-01-15T10:30:00",
    "products": [
      {
        "product_title": "Product Name",
        "product_url": "https://www.westside.com/products/...",
        "size_chart": {
          "headers": ["Size", "Bust (in)", "Waist (in)", "Hip (in)"],
          "rows": [
            {
              "Size": "S",
              "Bust (in)": "34",
              "Waist (in)": "28",
              "Hip (in)": "38"
            },
            {
              "Size": "M",
              "Bust (in)": "36",
              "Waist (in)": "30",
              "Hip (in)": "40"
            }
          ]
        }
      }
    ],
    "errors": []
  }
]
```

## Architecture

### Project Structure

```
assignment/
├── src/
│   ├── extractors/          # Store-specific and base extractors
│   │   ├── base.py         # Base extractor class
│   │   ├── generic_shopify.py  # Generic Shopify extractor
│   │   └── factory.py      # Extractor factory
│   ├── models/             # Data models
│   │   └── size_chart.py   # Pydantic models
│   ├── utils/              # Utility modules
│   │   ├── http_client.py  # HTTP client with retry logic
│   │   ├── parser.py       # HTML/JSON parsing utilities
│   │   └── rate_limiter.py # Rate limiting implementations
│   └── service.py          # Main service orchestration
├── tests/                  # Test files
├── docs/                   # Documentation
├── main.py                # CLI entry point
└── pyproject.toml         # Project configuration
```

### Key Components

1. **BaseExtractor**: Abstract base class defining the extraction interface
2. **GenericShopifyExtractor**: Works for most Shopify stores using multiple strategies
3. **HTTPClient**: Handles requests with retry logic and error handling
4. **RateLimiter**: Prevents hitting rate limits with dynamic adjustment
5. **SizeChartParser**: Intelligently finds and extracts size charts from HTML/JSON
6. **SizeChartExtractorService**: Orchestrates the extraction process

### Extraction Strategies

The extractor uses multiple strategies to find products:

1. **Products.json API**: Direct access to Shopify's product API
2. **Collections**: Browses store collections to find products
3. **Sitemap**: Falls back to sitemap for product discovery

### Size Chart Detection

The parser looks for size charts using:

1. **HTML Tables**: Identifies tables containing size-related keywords
2. **Confidence Scoring**: Ranks potential size charts by relevance
3. **JSON Data**: Extracts from structured data in page scripts
4. **Multiple Formats**: Handles various table structures and formats

## Testing

Run the test suite:

```bash
pytest tests/
```

Run with coverage:

```bash
pytest tests/ --cov=src --cov-report=html
```

## Extending the Service

### Adding Store-Specific Extractors

1. Create a new extractor in `src/extractors/`:

```python
from .base import BaseExtractor

class CustomStoreExtractor(BaseExtractor):
    async def get_product_urls(self) -> List[str]:
        # Custom logic for finding products
        pass

    async def extract_size_chart(self, product_url: str) -> Optional[Product]:
        # Custom extraction logic
        pass
```

2. Register it in `src/extractors/factory.py`:

```python
EXTRACTORS = {
    'customstore.com': CustomStoreExtractor,
}
```

### Customizing Extraction Logic

You can customize:

- Product discovery methods
- Size chart detection patterns
- Table parsing logic
- Rate limiting strategies

## Troubleshooting

### Common Issues

1. **No products found**: The store might block the products.json endpoint. The extractor will fall back to other methods.

2. **Rate limiting**: If you see 429 errors, increase the rate limit:

   ```bash
   python main.py store.com --rate-limit 3.0
   ```

3. **Timeout errors**: Increase the timeout for slow stores:

   ```bash
   python main.py store.com --timeout 60
   ```

4. **Missing size charts**: Some products might not have size charts. Check the debug logs:
   ```bash
   python main.py store.com --debug
   ```

### Debug Mode

Enable debug mode to see detailed logs:

```bash
python main.py westside.com --debug
```

This will show:

- HTTP requests being made
- Extraction strategies being used
- Size chart detection confidence scores
- Any errors encountered

## Performance Considerations

- **Concurrent Requests**: Adjust `--concurrent` based on your network capacity
- **Rate Limiting**: Start conservative (2-3 seconds) and decrease if successful
- **Product Limits**: Use `--max-products` to limit extraction scope
- **Memory Usage**: Large extractions may use significant memory; process in batches if needed
