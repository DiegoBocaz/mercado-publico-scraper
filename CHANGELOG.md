# Changelog

All notable changes to the Mercado Publico Scraper project will be documented in this file.

## [0.1.0] - 2024-02-06

### Added
- Initial implementation of Chilean Mercado Publico web scraper
- Dual extraction approach using BeautifulSoup and Selenium
- `BiddingDataExtractor` class for main extraction logic
- `WebpageNavigator` for browser automation
- `PageContentParser` for HTML parsing
- `ResultWriter` for JSON and CSV export
- `BiddingOpportunity` dataclass for tender information
- Asynchronous scraping with concurrent execution and rate limiting
- Comprehensive error handling with logging
- Configuration file (`config.ini`) for customization
- Unit tests for all major components
- Usage examples in `examples.py`
- Comprehensive README with installation and usage instructions

### Features
- Extract tender ID, title, organization name
- Extract number of offers/submissions
- Extract technical documents and attachments
- Export data to JSON format
- Export data to CSV format
- Configurable rate limiting
- Headless browser support
- Robust error handling with fallback values

### Testing
- 8 unit tests covering core functionality
- Tests for data extraction, parsing, and export
- Validation for data integrity and format

### Security
- No security vulnerabilities detected by CodeQL
- Safe extraction methods with try-except blocks
- No hardcoded credentials or sensitive data
