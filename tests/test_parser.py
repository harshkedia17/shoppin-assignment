"""
Tests for parser utilities.
"""
import pytest
from bs4 import BeautifulSoup

from src.utils.parser import SizeChartParser


class TestSizeChartParser:
    """Test cases for SizeChartParser."""

    def test_clean_text(self):
        """Test text cleaning functionality."""
        assert SizeChartParser.clean_text("  hello  world  ") == "hello world"
        assert SizeChartParser.clean_text("hello\n\tworld") == "hello world"
        assert SizeChartParser.clean_text("") == ""
        assert SizeChartParser.clean_text(None) == ""

    def test_extract_table_data_with_thead(self):
        """Test extracting data from table with thead."""
        html = """
        <table>
            <thead>
                <tr>
                    <th>Size</th>
                    <th>Chest</th>
                    <th>Waist</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>S</td>
                    <td>36</td>
                    <td>30</td>
                </tr>
                <tr>
                    <td>M</td>
                    <td>38</td>
                    <td>32</td>
                </tr>
            </tbody>
        </table>
        """
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table')

        headers, rows = SizeChartParser.extract_table_data(table)

        assert headers == ['Size', 'Chest', 'Waist']
        assert len(rows) == 2
        assert rows[0] == {'Size': 'S', 'Chest': '36', 'Waist': '30'}
        assert rows[1] == {'Size': 'M', 'Chest': '38', 'Waist': '32'}

    def test_extract_table_data_without_thead(self):
        """Test extracting data from table without thead."""
        html = """
        <table>
            <tr>
                <th>Size</th>
                <th>Length</th>
            </tr>
            <tr>
                <td>Small</td>
                <td>25"</td>
            </tr>
            <tr>
                <td>Medium</td>
                <td>27"</td>
            </tr>
        </table>
        """
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table')

        headers, rows = SizeChartParser.extract_table_data(table)

        assert headers == ['Size', 'Length']
        assert len(rows) == 2
        assert rows[0] == {'Size': 'Small', 'Length': '25"'}

    def test_find_size_charts(self):
        """Test finding size charts in HTML."""
        html = """
        <div>
            <h2>Product Details</h2>
            <table>
                <tr><td>Material</td><td>Cotton</td></tr>
            </table>
            
            <h2>Size Chart</h2>
            <table class="size-chart">
                <tr>
                    <th>Size</th>
                    <th>Bust (in)</th>
                    <th>Waist (in)</th>
                </tr>
                <tr>
                    <td>XS</td>
                    <td>32</td>
                    <td>26</td>
                </tr>
                <tr>
                    <td>S</td>
                    <td>34</td>
                    <td>28</td>
                </tr>
            </table>
        </div>
        """
        soup = BeautifulSoup(html, 'html.parser')

        potential_charts = SizeChartParser.find_size_charts(soup)

        assert len(potential_charts) >= 1
        # The size chart table should have higher confidence
        best_table, confidence = potential_charts[0]
        assert 'size-chart' in str(best_table.get('class', []))
        assert confidence > 0.5

    def test_parse_size_chart_from_json(self):
        """Test parsing size chart from JSON data."""
        # Test direct format
        data = {
            'sizeChart': {
                'headers': ['Size', 'Width'],
                'rows': [
                    {'Size': 'S', 'Width': '18'},
                    {'Size': 'M', 'Width': '20'}
                ]
            }
        }

        result = SizeChartParser.parse_size_chart_from_json(data)
        assert result is not None
        headers, rows = result
        assert headers == ['Size', 'Width']
        assert len(rows) == 2

        # Test array format
        data = {
            'sizing': [
                {'size': 'Small', 'chest': 36},
                {'size': 'Medium', 'chest': 38}
            ]
        }

        result = SizeChartParser.parse_size_chart_from_json(data)
        assert result is not None
        headers, rows = result
        assert 'size' in headers
        assert 'chest' in headers
        assert len(rows) == 2
