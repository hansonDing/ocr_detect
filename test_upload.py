#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test image upload and OCR processing functionality
"""

import requests
import os
import json

def test_image_upload():
    """Test image upload functionality"""
    # Server address
    url = "http://127.0.0.1:5000/upload"
    
    # Image file path
    image_path = "uploads/table_test_ocr_20250708_173524.png"
    
    if not os.path.exists(image_path):
        print(f"Error: Image file does not exist - {image_path}")
        return
    
    print("=" * 60)
    print("Testing Image Upload and OCR Processing")
    print("=" * 60)
    print(f"Uploading file: {image_path}")
    
    try:
        # Prepare files and data
        with open(image_path, 'rb') as f:
            files = {'file': (os.path.basename(image_path), f, 'image/png')}
            data = {
                'output_format': 'json',
                'image_type': 'document'
            }
            
            # Send request
            print("\nUploading and processing...")
            response = requests.post(url, files=files, data=data, timeout=30)
            
        print(f"\nResponse status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✓ Upload successful!")
            print("\nResponse content:")
            print("-" * 40)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # Check extracted information
            if 'extracted_info' in result:
                extracted = result['extracted_info']
                print("\nExtracted key information:")
                print("-" * 40)
                for key, value in extracted.items():
                    status = "✓" if value else "✗"
                    print(f"{status} {key}: {value}")
                    
                # Calculate extraction success rate
                total = len(extracted)
                success = sum(1 for v in extracted.values() if v)
                print(f"\nExtraction success rate: {success}/{total} ({success/total*100:.1f}%)")
                
            if 'record_id' in result:
                print(f"\nDatabase record ID: {result['record_id']}")
                
        else:
            print(f"\n✗ Upload failed: {response.status_code}")
            print(f"Error message: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("\n✗ Connection failed: Please ensure Flask server is running (http://127.0.0.1:5000)")
    except Exception as e:
        print(f"\n✗ Processing failed: {e}")
    
    print("\n" + "=" * 60)
    print("Test completed")
    print("=" * 60)

if __name__ == "__main__":
    test_image_upload()