#!/usr/bin/env python3
"""
Bot for extracting bidding data from Chilean government procurement website.
Uses dual approach: BeautifulSoup for static pages and Selenium for dynamic content.
"""
import asyncio
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import csv

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import aiohttp


@dataclass
class BiddingOpportunity:
    """Container for extracted bidding information"""
    identification_code: str = ""
    procurement_title: str = ""
    requesting_entity: str = ""
    submission_count: int = 0
    technical_attachments: List[Dict[str, str]] = field(default_factory=list)
    extraction_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    page_url: str = ""
    additional_metadata: Dict = field(default_factory=dict)


class WebpageNavigator:
    """Handles browser automation and page loading"""
    
    def __init__(self, headless_mode: bool = True):
        self.headless = headless_mode
        self.browser_instance = None
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def initialize_browser(self):
        """Start browser session with custom configuration"""
        chrome_settings = Options()
        if self.headless:
            chrome_settings.add_argument('--headless=new')
        chrome_settings.add_argument('--no-sandbox')
        chrome_settings.add_argument('--disable-dev-shm-usage')
        chrome_settings.add_argument('--disable-gpu')
        chrome_settings.add_argument('--window-size=1920,1080')
        
        driver_service = Service(ChromeDriverManager().install())
        self.browser_instance = webdriver.Chrome(service=driver_service, options=chrome_settings)
        self.logger.info("Browser session initialized successfully")
        
    def navigate_to_page(self, target_url: str, wait_seconds: int = 10):
        """Load webpage and wait for content"""
        if not self.browser_instance:
            self.initialize_browser()
        
        try:
            self.browser_instance.get(target_url)
            WebDriverWait(self.browser_instance, wait_seconds).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            self.logger.info(f"Successfully loaded: {target_url}")
            return True
        except TimeoutException:
            self.logger.error(f"Timeout loading: {target_url}")
            return False
            
    def cleanup(self):
        """Terminate browser session"""
        if self.browser_instance:
            self.browser_instance.quit()
            self.logger.info("Browser session terminated")


class PageContentParser:
    """Extract and parse HTML content"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def parse_html_structure(self, raw_html: str) -> BeautifulSoup:
        """Convert raw HTML to parseable structure"""
        return BeautifulSoup(raw_html, 'lxml')
        
    def extract_text_safely(self, element, selector: str, default_value: str = "") -> str:
        """Safely extract text from element with fallback"""
        try:
            found = element.select_one(selector)
            return found.get_text(strip=True) if found else default_value
        except Exception as e:
            self.logger.debug(f"Text extraction failed for {selector}: {e}")
            return default_value
            
    def extract_attribute_safely(self, element, selector: str, attr_name: str, default_value: str = "") -> str:
        """Safely extract attribute with fallback"""
        try:
            found = element.select_one(selector)
            return found.get(attr_name, default_value) if found else default_value
        except Exception as e:
            self.logger.debug(f"Attribute extraction failed for {selector}: {e}")
            return default_value


class BiddingDataExtractor:
    """Main extraction logic for tender information"""
    
    def __init__(self, base_portal_url: str = "https://www.mercadopublico.cl"):
        self.portal_base = base_portal_url
        self.nav = WebpageNavigator(headless_mode=True)
        self.parser = PageContentParser()
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def extract_single_tender(self, tender_id: str) -> Optional[BiddingOpportunity]:
        """Extract complete information for one tender"""
        tender_url = f"{self.portal_base}/Procurement/Modules/RFB/DetailsAcquisition.aspx?idlicitacion={tender_id}"
        
        try:
            if not self.nav.navigate_to_page(tender_url):
                return None
                
            page_markup = self.nav.browser_instance.page_source
            structured_content = self.parser.parse_html_structure(page_markup)
            
            opportunity = BiddingOpportunity()
            opportunity.identification_code = tender_id
            opportunity.page_url = tender_url
            
            # Extract title
            title_element = structured_content.select_one("#lblNombreLicitacion, .nombre-licitacion, h1")
            if title_element:
                opportunity.procurement_title = title_element.get_text(strip=True)
                
            # Extract organization
            org_element = structured_content.select_one("#lblOrganismo, .organismo-comprador")
            if org_element:
                opportunity.requesting_entity = org_element.get_text(strip=True)
                
            # Extract offer count
            offers_element = structured_content.select_one("#lblNumeroOfertas, .numero-ofertas")
            if offers_element:
                try:
                    opportunity.submission_count = int(offers_element.get_text(strip=True))
                except (ValueError, AttributeError):
                    opportunity.submission_count = 0
                    
            # Extract documents
            doc_links = structured_content.select("a[href*='Attachment'], a[href*='documento']")
            for link in doc_links:
                doc_info = {
                    "filename": link.get_text(strip=True),
                    "url": link.get('href', ''),
                    "type": "technical_document"
                }
                opportunity.technical_attachments.append(doc_info)
                
            self.logger.info(f"Successfully extracted tender: {tender_id}")
            return opportunity
            
        except Exception as e:
            self.logger.error(f"Failed to extract tender {tender_id}: {e}")
            return None
            
    async def extract_multiple_async(self, tender_ids: List[str]) -> List[BiddingOpportunity]:
        """Extract multiple tenders asynchronously"""
        results = []
        
        for tid in tender_ids:
            opportunity = self.extract_single_tender(tid)
            if opportunity:
                results.append(opportunity)
            await asyncio.sleep(0.5)  # Rate limiting
            
        return results
        
    def shutdown(self):
        """Cleanup resources"""
        self.nav.cleanup()


class ResultWriter:
    """Handles output to various file formats"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def write_to_json(self, opportunities: List[BiddingOpportunity], output_path: str):
        """Export data as JSON"""
        try:
            data_dicts = []
            for opp in opportunities:
                data_dicts.append({
                    "id": opp.identification_code,
                    "title": opp.procurement_title,
                    "entity": opp.requesting_entity,
                    "offers": opp.submission_count,
                    "documents": opp.technical_attachments,
                    "timestamp": opp.extraction_timestamp,
                    "url": opp.page_url
                })
                
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data_dicts, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"JSON output written to: {output_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to write JSON: {e}")
            
    def write_to_csv(self, opportunities: List[BiddingOpportunity], output_path: str):
        """Export data as CSV"""
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['id', 'title', 'entity', 'offers', 'document_count', 'timestamp', 'url']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for opp in opportunities:
                    writer.writerow({
                        'id': opp.identification_code,
                        'title': opp.procurement_title,
                        'entity': opp.requesting_entity,
                        'offers': opp.submission_count,
                        'document_count': len(opp.technical_attachments),
                        'timestamp': opp.extraction_timestamp,
                        'url': opp.page_url
                    })
                    
            self.logger.info(f"CSV output written to: {output_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to write CSV: {e}")


def configure_logging(log_level=logging.INFO):
    """Setup logging configuration"""
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('tender_extraction.log'),
            logging.StreamHandler()
        ]
    )
