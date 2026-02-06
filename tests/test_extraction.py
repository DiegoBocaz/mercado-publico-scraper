#!/usr/bin/env python3
"""
Unit tests for the Chilean Tender Bot extraction engine.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from cl_tender_bot.extraction_engine import (
    BiddingOpportunity,
    PageContentParser,
    ResultWriter,
    WebpageNavigator
)


class TestBiddingOpportunity(unittest.TestCase):
    """Test the BiddingOpportunity dataclass"""
    
    def test_initialization_with_defaults(self):
        """Test creating opportunity with default values"""
        opp = BiddingOpportunity()
        self.assertEqual(opp.identification_code, "")
        self.assertEqual(opp.procurement_title, "")
        self.assertEqual(opp.requesting_entity, "")
        self.assertEqual(opp.submission_count, 0)
        self.assertEqual(len(opp.technical_attachments), 0)
        self.assertIsInstance(opp.extraction_timestamp, str)
        
    def test_initialization_with_values(self):
        """Test creating opportunity with specific values"""
        opp = BiddingOpportunity(
            identification_code="TEST-123",
            procurement_title="Test Tender",
            requesting_entity="Test Org",
            submission_count=5
        )
        self.assertEqual(opp.identification_code, "TEST-123")
        self.assertEqual(opp.procurement_title, "Test Tender")
        self.assertEqual(opp.requesting_entity, "Test Org")
        self.assertEqual(opp.submission_count, 5)


class TestPageContentParser(unittest.TestCase):
    """Test HTML parsing functionality"""
    
    def setUp(self):
        self.parser = PageContentParser()
        
    def test_parse_html_structure(self):
        """Test HTML parsing"""
        html = "<html><body><h1>Test</h1></body></html>"
        soup = self.parser.parse_html_structure(html)
        self.assertIsNotNone(soup)
        self.assertEqual(soup.h1.text, "Test")
        
    def test_extract_text_safely_success(self):
        """Test safe text extraction when element exists"""
        from bs4 import BeautifulSoup
        html = "<div><span class='test'>Hello</span></div>"
        soup = BeautifulSoup(html, 'lxml')
        result = self.parser.extract_text_safely(soup, '.test')
        self.assertEqual(result, "Hello")
        
    def test_extract_text_safely_missing(self):
        """Test safe text extraction with missing element"""
        from bs4 import BeautifulSoup
        html = "<div><span>Hello</span></div>"
        soup = BeautifulSoup(html, 'lxml')
        result = self.parser.extract_text_safely(soup, '.missing', "default")
        self.assertEqual(result, "default")


class TestResultWriter(unittest.TestCase):
    """Test output writing functionality"""
    
    def setUp(self):
        self.writer = ResultWriter()
        
    def test_json_export_structure(self):
        """Test JSON export creates proper structure"""
        import tempfile
        import json
        
        opportunities = [
            BiddingOpportunity(
                identification_code="T1",
                procurement_title="Title 1",
                requesting_entity="Entity 1",
                submission_count=3
            )
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            output_path = f.name
            
        try:
            self.writer.write_to_json(opportunities, output_path)
            
            with open(output_path, 'r') as f:
                data = json.load(f)
                
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]['id'], "T1")
            self.assertEqual(data[0]['title'], "Title 1")
            self.assertEqual(data[0]['offers'], 3)
        finally:
            import os
            if os.path.exists(output_path):
                os.unlink(output_path)
                
    def test_csv_export_structure(self):
        """Test CSV export creates proper structure"""
        import tempfile
        import csv
        
        opportunities = [
            BiddingOpportunity(
                identification_code="T2",
                procurement_title="Title 2",
                requesting_entity="Entity 2",
                submission_count=4
            )
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            output_path = f.name
            
        try:
            self.writer.write_to_csv(opportunities, output_path)
            
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['id'], "T2")
            self.assertEqual(rows[0]['title'], "Title 2")
            self.assertEqual(rows[0]['offers'], "4")
        finally:
            import os
            if os.path.exists(output_path):
                os.unlink(output_path)


class TestWebpageNavigator(unittest.TestCase):
    """Test browser navigation functionality"""
    
    def test_initialization(self):
        """Test navigator initialization"""
        nav = WebpageNavigator(headless_mode=True)
        self.assertTrue(nav.headless)
        self.assertIsNone(nav.browser_instance)


if __name__ == '__main__':
    unittest.main()
