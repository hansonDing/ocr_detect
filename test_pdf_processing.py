#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test PDF processing functionality
"""

import requests
import os
import json

def test_pdf_upload():
    """Test PDF file upload and processing"""
    try:
        # Check if test PDF exists
        pdf_path = "test_document.pdf"
        if not os.path.exists(pdf_path):
            print(f"Test PDF file not found: {pdf_path}")
            return False
        
        print(f"Testing PDF processing with file: {pdf_path}")
        print(f"File size: {os.path.getsize(pdf_path)} bytes")
        
        # Prepare the upload request
        url = "http://localhost:5000/upload"
        
        with open(pdf_path, 'rb') as f:
            files = {'file': (pdf_path, f, 'application/pdf')}
            data = {
                'output_format': 'json'  # Test with JSON output format
            }
            
            print("Uploading PDF file to OCR service...")
            response = requests.post(url, files=files, data=data, timeout=60)
        
        print(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n=== PDF Processing Result ===")
            print(f"Success: {result.get('success', False)}")
            print(f"Message: {result.get('message', 'No message')}")
            print(f"File type: {result.get('file_type', 'Unknown')}")
            print(f"Output format: {result.get('output_format', 'Unknown')}")
            
            if result.get('success'):
                pdf_results = result.get('pdf_results', {})
                print(f"\nPDF Processing Details:")
                print(f"Total pages: {pdf_results.get('total_pages', 0)}")
                print(f"Successfully processed: {pdf_results.get('success_count', 0)}")
                print(f"Failed: {pdf_results.get('failed_count', 0)}")
                print(f"Output directory: {result.get('output_directory', 'Unknown')}")
                print(f"Combined result file: {result.get('combined_result_file', 'Unknown')}")
                
                # Show sample of combined OCR text
                combined_text = pdf_results.get('combined_ocr_text', '')
                if combined_text:
                    print(f"\nSample OCR Text (first 300 characters):")
                    print(f"{combined_text[:300]}...")
                
                # Show individual page results
                processed_results = pdf_results.get('processed_results', [])
                if processed_results:
                    print(f"\nIndividual Page Results:")
                    for page_result in processed_results[:3]:  # Show first 3 pages
                        print(f"  Page {page_result.get('page_number', 'Unknown')}: {page_result.get('status', 'Unknown')}")
                        if page_result.get('status') == 'success':
                            ocr_text = page_result.get('ocr_result', '')[:100]
                            print(f"    OCR Preview: {ocr_text}...")
                
                return True
            else:
                print(f"PDF processing failed: {result.get('message', 'Unknown error')}")
                return False
        else:
            print(f"HTTP Error: {response.status_code}")
            try:
                error_result = response.json()
                print(f"Error message: {error_result.get('message', 'Unknown error')}")
            except:
                print(f"Response text: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to OCR service. Make sure the Flask app is running on http://localhost:5000")
        return False
    except requests.exceptions.Timeout:
        print("Error: Request timed out. PDF processing may take longer for large files.")
        return False
    except Exception as e:
        print(f"Error testing PDF upload: {e}")
        return False

def test_pdf_libraries():
    """Test if PDF processing libraries are available"""
    print("Testing PDF processing libraries...")
    
    try:
        import fitz
        print("✓ PyMuPDF (fitz) is available")
        pymupdf_available = True
    except ImportError:
        print("✗ PyMuPDF (fitz) is not available")
        pymupdf_available = False
    
    try:
        from pdf2image import convert_from_path
        print("✓ pdf2image is available")
        pdf2image_available = True
    except ImportError:
        print("✗ pdf2image is not available")
        pdf2image_available = False
    
    if pymupdf_available or pdf2image_available:
        print("✓ PDF processing is supported")
        return True
    else:
        print("✗ No PDF processing libraries available")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("PDF Processing Test")
    print("=" * 60)
    
    # Test libraries
    if test_pdf_libraries():
        print("\n" + "=" * 60)
        # Test PDF upload
        success = test_pdf_upload()
        print("\n" + "=" * 60)
        if success:
            print("✓ PDF processing test completed successfully!")
        else:
            print("✗ PDF processing test failed!")
    else:
        print("Cannot proceed with PDF testing due to missing libraries.")