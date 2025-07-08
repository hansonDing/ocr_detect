#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test OCR recognition and information extraction for new images
"""

import requests
import os
import json
from datetime import datetime

def test_image_upload_and_extraction():
    """
    Test image upload and information extraction functionality
    """
    # Flask application URL
    base_url = "http://localhost:5000"
    
    # Use existing test image
    image_path = "uploads/test_pdf_20250708_195045.jpg"
    
    if not os.path.exists(image_path):
        print(f"Error: Image file does not exist - {image_path}")
        return
    
    print(f"Starting test for image: {image_path}")
    print("=" * 50)
    
    try:
        # Upload image for OCR recognition
        with open(image_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{base_url}/upload", files=files)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Image upload successful!")
            print(f"Processing time: {result.get('processing_time', 'N/A')} seconds")
            print(f"Extraction confidence: {result.get('extraction_confidence', 'N/A')}%")
            print(f"Model used: {result.get('model_used', 'N/A')}")
            
            # Display extracted information
            extracted_info = result.get('extracted_info', {})
            print("\n📋 Extracted Information:")
            print("-" * 30)
            
            fields = [
                ('customer_name', 'Customer Name'),
                ('customer_id', 'Customer ID'),
                ('transaction_id', 'Transaction ID'),
                ('transaction_amount', 'Transaction Amount'),
                ('payment_date', 'Payment Date'),
                ('document_timestamp', 'Document Timestamp'),
                ('customer_country', 'Customer Country')
            ]
            
            success_count = 0
            for field, label in fields:
                value = extracted_info.get(field, 'N/A')
                status = "✅" if value and value != 'N/A' else "❌"
                print(f"{status} {label}: {value}")
                if value and value != 'N/A':
                    success_count += 1
            
            print(f"\n📊 Extraction success rate: {success_count}/{len(fields)} ({success_count/len(fields)*100:.1f}%)")
            
            # Display original OCR text (first 200 characters)
            raw_text = result.get('raw_ocr_text', '')
            if raw_text:
                print(f"\n📝 Original OCR text (first 200 characters):")
                print("-" * 30)
                print(raw_text[:200] + "..." if len(raw_text) > 200 else raw_text)
            
            # Save results to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"output/test_result_{timestamp}.json"
            os.makedirs("output", exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 Results saved to: {output_file}")
            
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"Error message: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Unable to connect to Flask server, please ensure server is running")
        print("Please run: python app.py")
    except Exception as e:
        print(f"❌ Error occurred during testing: {str(e)}")

def check_database_records():
    """
    Check records in database
    """
    base_url = "http://localhost:5000"
    
    try:
        response = requests.get(f"{base_url}/database/records")
        if response.status_code == 200:
            records = response.json()
            print(f"\n📊 Total {len(records)} records in database")
            
            if records:
                latest_record = records[-1]  # Latest record
                print("\n🔍 Latest record:")
                print("-" * 30)
                print(f"ID: {latest_record.get('id')}")
                print(f"Filename: {latest_record.get('filename')}")
                print(f"Customer Name: {latest_record.get('customer_name')}")
                print(f"Extraction Confidence: {latest_record.get('extraction_confidence')}%")
                print(f"Processing Time: {latest_record.get('processing_time')} seconds")
        else:
            print(f"❌ Failed to get database records: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error occurred while checking database records: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting OCR system test")
    print("=" * 50)
    
    # Test image upload and extraction
    test_image_upload_and_extraction()
    
    # Check database records
    check_database_records()
    
    print("\n✅ Test completed!")