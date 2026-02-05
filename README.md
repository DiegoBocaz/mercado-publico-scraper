# mercado-publico-scraper
Web scraper for Chilean Mercado Publico licitaciones. Extracts tender details, offers, and technical documents.


## Features

- **Web Scraping**: Automatically extracts tender information from Mercado Publico
- **Document Extraction**: Downloads and processes attached technical documents
- **Comparative Analysis**: Analyzes provider bids and technical specifications
- **Data Export**: Exports tender data to multiple formats (JSON, CSV, Excel)
- **Headless Browser**: Uses Selenium for JavaScript-heavy page rendering
- **Error Handling**: Robust error management and retry logic
- **Logging**: Comprehensive logging for debugging and monitoring

## Requirements

- Python 3.8+
- Chrome/Chromium browser
- pip (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/DiegoBocaz/mercado-publico-scraper.git
cd mercado-publico-scraper
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root:
```
MERCADO_PUBLICO_BASE_URL=https://www.mercadopublico.cl
CHROME_PATH=/path/to/chrome
DOWNLOAD_DIR=./downloads
LOG_LEVEL=INFO
```

## Usage

### Basic Scraping
```python
from scraper import MercadoPublicoScraper

scraper = MercadoPublicoScraper()
tender = scraper.get_tender_details('2MOR0aWLwQi8224Am738OA==')
print(tender)
```

### Batch Processing
```python
from scraper import MercadoPublicoScraper

scraper = MercadoPublicoScraper()
tenders = scraper.search_tenders(keywords=['Data Warehouse', 'BI'])
for tender in tenders:
    scraper.extract_documents(tender)
```

## Project Structure

```
mercado-publico-scraper/
├── README.md
├── requirements.txt
├── .gitignore
├── LICENSE
├── setup.py
├── scraper/
│   ├── __init__.py
│   ├── main.py
│   ├── browser.py
│   ├── parser.py
│   ├── extractor.py
│   ├── analyzer.py
│   ├── models.py
│   └── utils.py
├── tests/
│   ├── __init__.py
│   ├── test_scraper.py
│   └── test_parser.py
└── examples/
    ├── example_tender_scraping.py
    ├── example_batch_processing.py
    └── example_document_analysis.py
```

## API Reference

### MercadoPublicoScraper

```python
class MercadoPublicoScraper:
    def __init__(self, headless=True, timeout=30)
    def get_tender_details(self, tender_id: str) -> dict
    def search_tenders(self, keywords: list) -> list
    def extract_documents(self, tender: dict) -> list
    def get_comparative_analysis(self, tender_id: str) -> dict
    def close()
```

## Limitations

- **CAPTCHA Protection**: Respects CAPTCHA and does not attempt to bypass them
- **Rate Limiting**: Implements delays between requests
- **Dynamic Content**: Uses Selenium for JavaScript rendering
- **Large Documents**: PDF extraction may be resource-intensive

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License

MIT License - See LICENSE file for details

## Author

**Diego Bocaz** - Full-stack Software Engineer  
GitHub: [@DiegoBocaz](https://github.com/DiegoBocaz)

## Disclaimer

This tool scrapes publicly available information from Mercado Publico. Users must ensure compliance with:
- Mercado Publico Terms of Service
- Chilean data protection laws
- Applicable robots.txt regulations
