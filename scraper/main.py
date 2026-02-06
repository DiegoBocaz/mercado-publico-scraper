#!/usr/bin/env python3
"""
Main entry point for the Mercado Publico Scraper CLI
"""

import click
import sys
from loguru import logger

# Configure logging
logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>")


@click.group()
def cli():
    """Mercado Publico Scraper - Web scraper for Chilean government procurement."""
    pass


@cli.command()
@click.option('--tender-id', required=True, help='Tender ID to scrape')
@click.option('--output', type=click.Path(), help='Output file path')
def scrape_tender(tender_id, output):
    """Scrape a single tender from Mercado Publico."""
    try:
        logger.info(f"Starting to scrape tender: {tender_id}")
        # Implementation will be added
        logger.success(f"Successfully scraped tender: {tender_id}")
    except Exception as e:
        logger.error(f"Error scraping tender: {e}")
        sys.exit(1)


@cli.command()
@click.option('--keywords', multiple=True, help='Keywords to search for')
@click.option('--limit', type=int, default=10, help='Maximum number of results')
def search_tenders(keywords, limit):
    """Search for tenders matching keywords."""
    try:
        logger.info(f"Searching for tenders with keywords: {keywords}")
        # Implementation will be added
        logger.success(f"Found tenders matching: {keywords}")
    except Exception as e:
        logger.error(f"Error searching tenders: {e}")
        sys.exit(1)


@cli.command()
@click.option('--tender-id', required=True, help='Tender ID')
def extract_documents(tender_id):
    """Extract documents from a tender."""
    try:
        logger.info(f"Extracting documents from tender: {tender_id}")
        # Implementation will be added
        logger.success(f"Documents extracted from tender: {tender_id}")
    except Exception as e:
        logger.error(f"Error extracting documents: {e}")
        sys.exit(1)


if __name__ == '__main__':
    cli()
