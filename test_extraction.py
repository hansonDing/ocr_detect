#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test information extraction functionality
"""

from database import extract_key_information, save_to_database
import os

# Simulate OCR recognition results (based on user-provided image content)
sample_ocr_text = """
Client Payment Report Mock

FieldName                Value
Customer Name           Wu Gang
Customer ID             1050843
Transaction ID          500007826
Transaction Amount      6750.00
Payment Date            2025-01-05
Document Timestamp      2025-07-08 18:50:48
Customer Country        US
"""

def test_extraction():
    """Test information extraction functionality"""
    print("=" * 60)
    print("Testing OCR Information Extraction")
    print("=" * 60)
    
    print("\nOriginal OCR text:")
    print("-" * 40)
    print(sample_ocr_text)
    
    # Extract key information
    extracted_info = extract_key_information(sample_ocr_text)
    
    print("\nExtracted key information:")
    print("-" * 40)
    for key, value in extracted_info.items():
        status = "✓" if value else "✗"
        print(f"{status} {key}: {value}")
    
    # Calculate extraction success rate
    total_fields = len(extracted_info)
    extracted_fields = sum(1 for v in extracted_info.values() if v is not None)
    success_rate = (extracted_fields / total_fields) * 100
    
    print(f"\nExtraction statistics:")
    print("-" * 40)
    print(f"Total fields: {total_fields}")
    print(f"Successfully extracted: {extracted_fields}")
    print(f"Success rate: {success_rate:.1f}%")
    
    # Save to database
    try:
        record_id = save_to_database(
            filename="test_payment_report.png",
            file_path="/test/path/test_payment_report.png",
            ocr_text=sample_ocr_text,
            model_used="Test",
            extracted_info=extracted_info
        )
        print(f"\n✓ Data saved to database, record ID: {record_id}")
    except Exception as e:
        print(f"\n✗ Failed to save to database: {e}")
    
    print("\n=" * 60)
    print("Test completed")
    print("=" * 60)

if __name__ == "__main__":
    test_extraction()