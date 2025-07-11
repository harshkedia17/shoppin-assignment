"""
Gemini 2.5 Flash integration for extracting structured size chart data from images.
"""
import asyncio
import base64
import io
import logging
import json
from typing import Optional, Dict, Any
import aiohttp
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO

from src.models.size_chart import GeminiSizeChartExtractionResult, SizeChart, SizeChartGemini

logger = logging.getLogger(__name__)


class GeminiSizeChartExtractor:
    """Extract structured size chart data from images using Gemini 2.5 Flash."""

    # System prompt for size chart extraction
    SYSTEM_PROMPT = """You are an expert at extracting size chart data from images. Your task is to analyze the provided image and extract size chart information in a structured format.

Instructions:
1. Identify if the image contains a size chart
2. Extract ALL column headers exactly as they appear (e.g., "Size", "Bust", "Waist", "Hip", "Length", etc.)
3. Extract ALL rows of data, preserving the exact values
4. Handle various formats: tables, grids, or text-based size charts
5. Include units if specified (e.g., "in", "cm", "inches", "centimeters")
6. If multiple size charts exist (e.g., US/UK/EU sizes), extract all of them
7. If no size chart is found, return null

Important:
- Preserve exact text from the image (don't convert or standardize)
- Include ALL columns, even if they seem redundant
- Keep original formatting of sizes (S, M, L or 36, 38, 40, etc.)
- Extract numeric ranges as they appear (e.g., "32-34" not just "33")
"""

    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash-exp"):
        """
        Initialize the Gemini extractor.

        Args:
            api_key: Google AI API key
            model_name: Gemini model to use (default: gemini-2.0-flash-exp)
        """
        self.client = genai.Client(
            api_key=api_key,
        )
        self.model_name = model_name

    async def generate_content(self, image_data: bytes, mime_type: str) -> Optional[GeminiSizeChartExtractionResult]:
        generate_content_config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=GeminiSizeChartExtractionResult,
            system_instruction=[types.Part.from_text(text=self.SYSTEM_PROMPT)]
        )
        contents = [
            types.Part.from_bytes(data=image_data, mime_type=mime_type),
            types.Part.from_text(
                text="Analyze this image and extract the size chart data according to the JSON schema.")
        ]
        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=generate_content_config
        )
        if response.parsed:
            return response.parsed
        return None

    async def extract_table(self, image_url: str) -> Optional[SizeChart]:
        try:
            if image_url.startswith('//'):
                image_url = f'https:{image_url}'
            
            if image_url.startswith('data:image/'):
                base64_data = image_url.split(',')[1]
                image_bytes = base64.b64decode(base64_data)
                image = Image.open(BytesIO(image_bytes))

            else:

                if not image_url.startswith(('http://', 'https://')):
                    image_url = f'https://{image_url}'

                image_url = image_url.strip()

                async with aiohttp.ClientSession() as client:
                    async with client.get(image_url) as response:
                        if response.status != 200:
                            logger.error(f"Failed to fetch image from {image_url}: {response.status}")
                            return None
                            
                        image_bytes = await response.read()
                        image = Image.open(io.BytesIO(image_bytes))
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG')
            image_bytes_for_api = buffer.getvalue()
            result = await self.generate_content(image_bytes_for_api, 'image/jpeg')
            if result and result.has_size_chart and result.size_chart:
                converted_size_chart = self._convert_to_standard_format(result.size_chart)
                return converted_size_chart

            return None

        except Exception as e:
            logger.error(f"Failed to extract size chart from image: {e}")
            return None

    def _convert_to_standard_format(self, gemini_size_chart: SizeChartGemini) -> SizeChart:

        headers = gemini_size_chart.headers

        converted_rows = []
        for row in gemini_size_chart.rows:
            row_dict = {}
            for kv_pair in row.columns:
                row_dict[kv_pair.key] = kv_pair.value
            converted_rows.append(row_dict)

        return SizeChart(headers=headers, rows=converted_rows)

