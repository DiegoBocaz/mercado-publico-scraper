# Usage Guide for Mercado Publico Scraper

This guide provides practical instructions for using the scraper with real tender data from mercadopublico.cl.

## Finding Tender IDs

Tender IDs can be found on the Mercado Publico website:
1. Visit https://www.mercadopublico.cl
2. Search for tenders using the search functionality
3. Click on a tender to view its details
4. The tender ID is typically shown in the URL or at the top of the page
   - Format: XXXX-XXX-LXXX (e.g., "1234-567-L123")

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/DiegoBocaz/mercado-publico-scraper.git
cd mercado-publico-scraper

# Install dependencies
pip install -r requirements.txt
```

### 2. Basic Usage

Create a Python script:

```python
#!/usr/bin/env python3
import asyncio
from cl_tender_bot.extraction_engine import (
    BiddingDataExtractor, 
    ResultWriter, 
    configure_logging
)

async def main():
    configure_logging()
    extractor = BiddingDataExtractor()
    
    try:
        # Replace with actual tender IDs from mercadopublico.cl
        tender_ids = ["YOUR-TENDER-ID-HERE"]
        
        results = await extractor.extract_multiple_async(tender_ids)
        
        if results:
            writer = ResultWriter()
            writer.write_to_json(results, "output/tenders.json")
            writer.write_to_csv(results, "output/tenders.csv")
            print(f"Extracted {len(results)} tenders successfully")
    finally:
        extractor.shutdown()

asyncio.run(main())
```

### 3. Customizing Extraction

#### Adjust Concurrency

```python
# Extract up to 5 tenders concurrently
results = await extractor.extract_multiple_async(tender_ids, max_concurrent=5)
```

#### Change Base URL

```python
# Use a different base URL if needed
extractor = BiddingDataExtractor(base_portal_url="https://www.mercadopublico.cl")
```

#### Control Browser Behavior

```python
from cl_tender_bot.extraction_engine import WebpageNavigator

# Use non-headless mode for debugging
nav = WebpageNavigator(headless_mode=False)
```

## Configuration

Edit `config.ini` to customize default settings:

```ini
[extraction]
base_url = https://www.mercadopublico.cl
headless = true
page_timeout = 10
request_delay = 0.5

[output]
output_dir = ./output
formats = json,csv

[logging]
level = INFO
log_file = tender_extraction.log
```

## Output Format

### JSON
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

### CSV
```
id,title,entity,offers,document_count,timestamp,url
1234-567-L123,Tender Title,Government Organization,5,3,2024-01-15T10:30:00,https://...
```

## Troubleshooting

### Issue: Browser doesn't start
**Solution**: Make sure Chrome/Chromium is installed. The webdriver-manager will auto-install chromedriver.

### Issue: Timeout errors
**Solution**: Increase the `page_timeout` in config.ini or when calling `navigate_to_page()`.

### Issue: No data extracted
**Solution**: 
- Verify the tender ID is correct
- Check if the website structure has changed
- Enable DEBUG logging to see detailed error messages

### Issue: Rate limiting / blocked requests
**Solution**: Increase the `request_delay` in config.ini to be more respectful of server resources.

## Best Practices

1. **Rate Limiting**: Always use reasonable delays between requests (0.5-1 second minimum)
2. **Error Handling**: Check logs for failed extractions and handle them appropriately
3. **Batch Processing**: Process tenders in batches to avoid overwhelming the server
4. **Data Validation**: Always validate extracted data before using it downstream
5. **Logging**: Keep logs to track extraction history and debug issues

## Examples

See `examples.py` for complete working examples:
- Single tender extraction
- Batch extraction with async
- Custom data processing
- Error handling patterns

## Legal and Ethical Considerations

- Always respect the website's terms of service
- Use reasonable rate limiting
- Don't overload the server with too many requests
- Consider the website's robots.txt file
- Use the data responsibly and according to applicable laws

## Support

For issues, questions, or contributions, please visit:
https://github.com/DiegoBocaz/mercado-publico-scraper
