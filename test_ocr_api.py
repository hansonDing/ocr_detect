#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test OCR API direct call
"""

import os
import base64
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OCR API configuration
OCR_API_KEY = os.getenv('OCR_API_KEY', 'sk-test')
OCR_API_BASE = os.getenv('OCR_API_BASE', 'https://api-inference.modelscope.cn/v1')
OCR_MODEL = os.getenv('OCR_MODEL', 'OCR')

def image_to_base64(image_path):
    """Convert image to base64 encoding"""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        raise Exception(f"Image encoding failed: {str(e)}")

def test_ocr_api_direct():
    """Test OCR API direct call"""
    print("=" * 60)
    print("Testing OCR API Direct Call")
    print("=" * 60)
    
    # Configuration information
    print(f"API Base: {OCR_API_BASE}")
    print(f"API Key: {OCR_API_KEY[:10]}...")
    print(f"Model: {OCR_MODEL}")
    
    # Image path
    image_path = "uploads/table_test_ocr_20250708_173524.png"
    
    if not os.path.exists(image_path):
        print(f"\nError: Image file does not exist - {image_path}")
        return
    
    print(f"\nTest image: {image_path}")
    
    try:
        # Initialize client
        print("\n1. Initializing OCR client...")
        ocr_client = OpenAI(
            api_key=OCR_API_KEY,
            base_url=OCR_API_BASE
        )
        print("✓ Client initialization successful")
        
        # Test connection
        print("\n2. Testing API connection...")
        try:
            models = ocr_client.models.list()
            print(f"✓ API connection successful, available models: {[model.id for model in models.data[:5]]}...")
        except Exception as e:
            print(f"✗ API connection test failed: {e}")
            return
        
        # Convert image to base64
        print("\n3. Converting image to base64...")
        base64_image = image_to_base64(image_path)
        print(f"✓ Image conversion successful, size: {len(base64_image)} characters")
        
        # Call OCR API
        print("\n4. Calling OCR API for text recognition...")
        
        prompt_text = "Please recognize all text content in this image and output it exactly as it appears. Focus on extracting structured information like customer details, transaction information, dates, and amounts."
        
        response = ocr_client.chat.completions.create(
            model=OCR_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt_text
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=2000,
            temperature=0.1
        )
        
        if response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content
            if content:
                print("✓ OCR recognition successful!")
                print("\nRecognition result:")
                print("-" * 40)
                print(content.strip())
                print("-" * 40)
                
                # Test information extraction
                print("\n5. Testing information extraction...")
                from database import extract_key_information
                extracted_info = extract_key_information(content.strip())
                
                print("Extracted key information:")
                for key, value in extracted_info.items():
                    status = "✓" if value else "✗"
                    print(f"{status} {key}: {value}")
                    
            else:
                print("✗ OCR returned empty result")
        else:
            print("✗ OCR API response format error")
            
    except Exception as e:
        print(f"\n✗ OCR API call failed: {e}")
        import traceback
        print("Detailed error information:")
        print(traceback.format_exc())
    
    print("\n" + "=" * 60)
    print("Test completed")
    print("=" * 60)

if __name__ == "__main__":
    test_ocr_api_direct()