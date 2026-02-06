#!/usr/bin/env python3
"""
Advanced usage examples for the Chilean Tender Bot.
Demonstrates various extraction scenarios and customization options.
"""
import asyncio
import logging
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from cl_tender_bot.extraction_engine import (
    BiddingDataExtractor,
    ResultWriter,
    BiddingOpportunity,
    configure_logging
)


def example_single_extraction():
    """Example: Extract a single tender synchronously"""
    print("\n=== Example 1: Single Tender Extraction ===\n")
    
    configure_logging(logging.INFO)
    extractor = BiddingDataExtractor()
    
    try:
        # Extract single tender
        tender_id = "1234-567-L123"
        result = extractor.extract_single_tender(tender_id)
        
        if result:
            print(f"Extracted tender: {result.identification_code}")
            print(f"Title: {result.procurement_title}")
            print(f"Organization: {result.requesting_entity}")
            print(f"Offers: {result.submission_count}")
            print(f"Documents: {len(result.technical_attachments)}")
        else:
            print("Failed to extract tender")
            
    finally:
        extractor.shutdown()


async def example_batch_extraction():
    """Example: Extract multiple tenders asynchronously"""
    print("\n=== Example 2: Batch Tender Extraction ===\n")
    
    configure_logging(logging.INFO)
    extractor = BiddingDataExtractor()
    
    try:
        tender_ids = [
            "1234-567-L123",
            "2345-678-L234",
            "3456-789-L345",
            "4567-890-L456",
            "5678-901-L567"
        ]
        
        print(f"Extracting {len(tender_ids)} tenders...")
        results = await extractor.extract_multiple_async(tender_ids)
        
        print(f"\nSuccessfully extracted: {len(results)}/{len(tender_ids)} tenders")
        
        # Export results
        writer = ResultWriter()
        writer.write_to_json(results, "batch_export.json")
        writer.write_to_csv(results, "batch_export.csv")
        
        print("Results exported to batch_export.json and batch_export.csv")
        
    finally:
        extractor.shutdown()


async def example_custom_export():
    """Example: Custom data processing and export"""
    print("\n=== Example 3: Custom Data Processing ===\n")
    
    configure_logging(logging.WARNING)  # Less verbose
    extractor = BiddingDataExtractor()
    
    try:
        tender_ids = ["1234-567-L123", "2345-678-L234"]
        results = await extractor.extract_multiple_async(tender_ids)
        
        # Custom processing: filter tenders with more than 3 offers
        high_interest = [r for r in results if r.submission_count > 3]
        
        print(f"Total tenders: {len(results)}")
        print(f"High interest tenders (>3 offers): {len(high_interest)}")
        
        if high_interest:
            writer = ResultWriter()
            writer.write_to_json(high_interest, "high_interest_tenders.json")
            print("\nHigh interest tenders exported")
            
    finally:
        extractor.shutdown()


def example_error_handling():
    """Example: Robust error handling"""
    print("\n=== Example 4: Error Handling ===\n")
    
    configure_logging(logging.DEBUG)
    extractor = BiddingDataExtractor()
    
    try:
        # Mix of valid and potentially invalid tender IDs
        tender_ids = ["INVALID-ID", "1234-567-L123", "ANOTHER-BAD-ID"]
        
        successful_extractions = []
        failed_extractions = []
        
        for tid in tender_ids:
            result = extractor.extract_single_tender(tid)
            if result:
                successful_extractions.append(result)
            else:
                failed_extractions.append(tid)
                
        print(f"Successful: {len(successful_extractions)}")
        print(f"Failed: {len(failed_extractions)}")
        
        if failed_extractions:
            print(f"\nFailed tender IDs: {', '.join(failed_extractions)}")
            
    finally:
        extractor.shutdown()


def main():
    """Run all examples"""
    print("=" * 70)
    print("Chilean Tender Bot - Usage Examples")
    print("=" * 70)
    
    # Example 1: Single extraction
    # example_single_extraction()
    
    # Example 2: Batch extraction
    # asyncio.run(example_batch_extraction())
    
    # Example 3: Custom export
    # asyncio.run(example_custom_export())
    
    # Example 4: Error handling
    # example_error_handling()
    
    print("\n" + "=" * 70)
    print("Uncomment examples in main() to run specific scenarios")
    print("=" * 70)


if __name__ == "__main__":
    main()
