# Mercado Publico Scraper

Web scraper for extracting tender information from Chilean Mercado Publico (mercadopublico.cl).

## Features

- **Dual Extraction Approach**: Uses both BeautifulSoup for static content and Selenium for dynamic pages
- **Async Support**: Asynchronous scraping for improved performance
- **Comprehensive Data Extraction**: 
  - Tender ID
  - Tender name/title
  - Requesting organization
  - Number of offers/submissions
  - Technical documents and attachments
- **Error Handling**: Robust error handling with logging
- **Multiple Export Formats**: Export to JSON and CSV
- **Rate Limiting**: Built-in delays to respect server resources

## Installation

1. Clone the repository:
```bash
git clone https://github.com/DiegoBocaz/mercado-publico-scraper.git
cd mercado-publico-scraper
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Run the demo script with example tender IDs:

```bash
python run_bot.py
```

### Programmatic Usage

```python
import asyncio
from cl_tender_bot.extraction_engine import (
    BiddingDataExtractor,
    ResultWriter,
    configure_logging
)

async def extract_tenders():
    configure_logging()
    
    # Initialize extractor
    extractor = BiddingDataExtractor()
    
    # Define tender IDs to extract
    tender_ids = ["1234-567-L123", "5678-901-L456"]
    
    try:
        # Extract tenders
        results = await extractor.extract_multiple_async(tender_ids)
        
        # Export results
        writer = ResultWriter()
        writer.write_to_json(results, "tenders.json")
        writer.write_to_csv(results, "tenders.csv")
        
    finally:
        extractor.shutdown()

asyncio.run(extract_tenders())
```

## Architecture

The scraper consists of several key components:

- **WebpageNavigator**: Manages Selenium browser automation
- **PageContentParser**: Handles HTML parsing with BeautifulSoup
- **BiddingDataExtractor**: Core extraction logic
- **ResultWriter**: Exports data to JSON/CSV formats
- **BiddingOpportunity**: Data class for tender information

## Configuration

Edit `config.ini` to customize:
- Browser settings (headless mode, timeouts)
- Rate limiting delays
- Output formats and locations
- Logging levels

## Output Format

### JSON Output
```json
[
  {
    "id": "1234-567-L123",
    "title": "Tender Title",
    "entity": "Government Organization",
    "offers": 5,
    "documents": [
      {
        "filename": "technical_specs.pdf",
        "url": "https://...",
        "type": "technical_document"
      }
    ],
    "timestamp": "2024-01-15T10:30:00",
    "url": "https://..."
  }
]
```

### CSV Output
Includes columns: id, title, entity, offers, document_count, timestamp, url

## Requirements

- Python 3.8+
- Chrome/Chromium browser (installed automatically via webdriver-manager)
- See `requirements.txt` for Python dependencies

## License

See LICENSE file for details.
