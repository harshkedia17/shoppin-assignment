import re
import logging
from typing import List, Dict, Optional, Any, Tuple
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)


class SizeChartParser:

    @staticmethod
    def clean_text(text: str) -> str:
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text.strip())
        text = re.sub(r'[\u200b\u00a0]', ' ', text)
        return text.strip()

    @staticmethod
    def extract_table_data(table: Tag) -> Tuple[List[str], List[Dict[str, str]]]:
        headers = []
        rows = []

        thead = table.find('thead')
        if thead:
            header_row = thead.find('tr')
            if header_row:
                headers = [
                    SizeChartParser.clean_text(th.get_text())
                    for th in header_row.find_all(['th', 'td'])
                ]

        if not headers:
            first_row = table.find('tr')
            if first_row:
                cells = first_row.find_all(['th', 'td'])
                if cells and (cells[0].name == 'th' or all(cell.get('class') and 'header' in ' '.join(cell.get('class', [])) for cell in cells)):
                    headers = [SizeChartParser.clean_text(
                        cell.get_text()) for cell in cells]

        tbody = table.find('tbody') or table
        for row in tbody.find_all('tr'):
            cells = row.find_all(['td', 'th'])
            if not cells:
                continue

            if headers and len(cells) == len(headers):
                cell_texts = [SizeChartParser.clean_text(
                    cell.get_text()) for cell in cells]
                if cell_texts == headers:
                    continue


            row_data = {}
            for i, cell in enumerate(cells):
                if i >= len(headers):
                    continue

                header = headers[i]


                default_span = cell.find('span', class_='default')
                if default_span:

                    value = SizeChartParser.clean_text(default_span.get_text())
                    if header != headers[0]:  # If not the size column
                        value = f"{value} CM"
                else:
                    value = SizeChartParser.clean_text(cell.get_text())

                row_data[header] = value

            if row_data:
                rows.append(row_data)

        return headers, rows

    @staticmethod
    def find_size_charts(soup: BeautifulSoup) -> List[Tuple[Tag, float]]:

        size_keywords = [
            'size', 'chart', 'measurement', 'dimension', 'sizing',
            'fit', 'length', 'width', 'chest', 'waist', 'hip',
            'shoulder', 'sleeve', 'bust', 'inseam', 'size guide'
        ]

        size_patterns = [
            re.compile(r'\b(xs|s|m|l|xl|xxl|xxxl|small|medium|large)\b', re.I),
            re.compile(r'\b\d{2,3}\s*(cm|inch|in|")\b', re.I),
            re.compile(r'\b(chest|waist|hip|bust)\s*[:=]?\s*\d+', re.I)
        ]

        potential_tables = []

        for table in soup.find_all('table'):
            confidence = 0.0

            table_text = table.get_text().lower()
            for keyword in size_keywords:
                if keyword in table_text:
                    confidence += 0.1

            for pattern in size_patterns:
                matches = pattern.findall(table_text)
                if matches:
                    confidence += 0.2 * min(len(matches) / 5, 1.0)

            headers, rows = SizeChartParser.extract_table_data(table)
            if headers and rows:
                header_text = ' '.join(headers).lower()
                for keyword in size_keywords:
                    if keyword in header_text:
                        confidence += 0.2

                if 2 <= len(rows) <= 20:
                    confidence += 0.1

            parent = table.parent
            while parent and parent.name != 'body':
                parent_text = ' '.join(parent.get('class', [])) + ' ' + parent.get('id', '')
                if any(keyword in parent_text.lower() for keyword in ['size', 'chart', 'sizing']):
                    confidence += 0.3
                    break
                parent = parent.parent

            if confidence > 0.3:
                potential_tables.append((table, confidence))

        potential_tables.sort(key=lambda x: x[1], reverse=True)

        return potential_tables

    @staticmethod
    def parse_size_chart_from_json(data: Dict[str, Any]) -> Optional[Tuple[List[str], List[Dict[str, str]]]]:

        if isinstance(data, dict):
            for key in ['sizeChart', 'size_chart', 'sizing', 'measurements']:
                if key in data:
                    chart_data = data[key]
                    if isinstance(chart_data, dict) and 'headers' in chart_data and 'rows' in chart_data:
                        return chart_data['headers'], chart_data['rows']
                    elif isinstance(chart_data, list) and chart_data:   
                        if isinstance(chart_data[0], dict):
                            headers = list(chart_data[0].keys())
                            rows = chart_data
                            return headers, rows

        return None
