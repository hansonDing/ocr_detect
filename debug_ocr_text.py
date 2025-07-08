#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug OCR text extraction
"""

import requests
import json

def get_latest_ocr_result():
    """Get the latest OCR result"""
    try:
        # Get latest record from Flask application
        response = requests.get('http://localhost:5000/database/records')
        print(f"API response status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"API response data: {data}")
            
            if data.get('records'):
                latest_record = data['records'][0]  # Latest record
                print(f"Latest record: {latest_record}")
                
                # Try different field names
                ocr_text = latest_record.get('raw_ocr_text') or latest_record.get('ocr_text', '')
                print(f"OCR text length: {len(ocr_text) if ocr_text else 0}")
                return ocr_text
            else:
                print("No records found")
        else:
            print(f"API request failed: {response.text}")
    except Exception as e:
        print(f"Failed to get records: {e}")
        import traceback
        print(traceback.format_exc())
    return None

def analyze_text_structure(text):
    """Analyze text structure"""
    if not text:
        print("No text to analyze")
        return
    
    print("Original OCR text:")
    print("=" * 60)
    print(repr(text))  # Display raw string including newlines etc.
    print("=" * 60)
    
    print("\nFormatted display:")
    print("-" * 40)
    print(text)
    print("-" * 40)
    
    print("\nLine by line analysis:")
    lines = text.split('\n')
    for i, line in enumerate(lines):
        print(f"Line {i+1}: {repr(line)}")
    
    print("\nLooking for table structure:")
    for i, line in enumerate(lines):
        if '|' in line:
            print(f"Table row {i+1}: {line}")
            parts = [part.strip() for part in line.split('|')]
            print(f"  After splitting: {parts}")

def test_extraction_with_debug(text):
    """Test extraction function and display debug information"""
    from database import extract_key_information, extract_from_table_format
    
    print("\nTesting table format extraction:")
    table_result = extract_from_table_format(text)
    print("Table extraction result:")
    for key, value in table_result.items():
        status = "✓" if value else "✗"
        print(f"  {status} {key}: {value}")
    
    print("\nTesting full extraction function:")
    full_result = extract_key_information(text)
    print("Full extraction result:")
    for key, value in full_result.items():
        status = "✓" if value else "✗"
        print(f"  {status} {key}: {value}")

if __name__ == "__main__":
    print("Debug OCR Text Extraction")
    print("=" * 60)
    
    # Get latest OCR result
    ocr_text = get_latest_ocr_result()
    
    if ocr_text:
        analyze_text_structure(ocr_text)
        test_extraction_with_debug(ocr_text)
    else:
        print("Unable to get OCR text, please upload an image first")