#!/usr/bin/env python3
"""
Entry point script for running the Chilean tender extraction bot.
Demonstrates usage of the extraction engine with example tender IDs.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cl_tender_bot.extraction_engine import (
    BiddingDataExtractor,
    ResultWriter,
    configure_logging
)


async def run_extraction_demo():
    """Demonstration of tender extraction workflow"""
    configure_logging()
    
    # Example tender IDs (these would be real IDs from mercadopublico.cl)
    sample_tender_ids = [
        "1234-567-L123",
        "5678-901-L456",
        "9012-345-L789"
    ]
    
    print("=" * 60)
    print("Chilean Tender Bot - Extraction Demo")
    print("=" * 60)
    
    extractor = BiddingDataExtractor()
    
    try:
        print(f"\nExtracting {len(sample_tender_ids)} tenders...")
        results = await extractor.extract_multiple_async(sample_tender_ids)
        
        print(f"\nSuccessfully extracted {len(results)} tenders")
        
        if results:
            writer = ResultWriter()
            
            # Write outputs
            json_output = "extracted_tenders.json"
            csv_output = "extracted_tenders.csv"
            
            writer.write_to_json(results, json_output)
            writer.write_to_csv(results, csv_output)
            
            print(f"\nResults saved to:")
            print(f"  - {json_output}")
            print(f"  - {csv_output}")
            
            # Display summary
            print("\n" + "=" * 60)
            print("Extraction Summary:")
            print("=" * 60)
            for opp in results:
                print(f"\nID: {opp.identification_code}")
                print(f"Title: {opp.procurement_title}")
                print(f"Entity: {opp.requesting_entity}")
                print(f"Offers: {opp.submission_count}")
                print(f"Documents: {len(opp.technical_attachments)}")
        else:
            print("\nNo tenders were successfully extracted.")
            
    finally:
        extractor.shutdown()
        print("\nExtraction complete. Resources cleaned up.")


if __name__ == "__main__":
    asyncio.run(run_extraction_demo())
