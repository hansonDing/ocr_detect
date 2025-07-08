#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix OCR model configuration
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OCR API configuration
OCR_API_KEY = os.getenv('OCR_API_KEY', 'sk-test')
OCR_API_BASE = os.getenv('OCR_API_BASE', 'https://api-inference.modelscope.cn/v1')

def find_working_ocr_model():
    """Find available OCR models"""
    print("=" * 60)
    print("Finding available OCR models")
    print("=" * 60)
    
    try:
        # Initialize client
        ocr_client = OpenAI(
            api_key=OCR_API_KEY,
            base_url=OCR_API_BASE
        )
        
        # Get all available models
        print("Getting available model list...")
        models = ocr_client.models.list()
        
        # Find OCR related models
        ocr_models = []
        vision_models = []
        
        for model in models.data:
            model_id = model.id.lower()
            if 'ocr' in model_id:
                ocr_models.append(model.id)
            elif any(keyword in model_id for keyword in ['vision', 'visual', 'image', 'multimodal', 'qwen', 'gpt']):
                vision_models.append(model.id)
        
        print(f"\nFound {len(ocr_models)} OCR models:")
        for i, model in enumerate(ocr_models[:10], 1):
            print(f"{i}. {model}")
            
        print(f"\nFound {len(vision_models)} vision models:")
        for i, model in enumerate(vision_models[:10], 1):
            print(f"{i}. {model}")
        
        # Recommended models
        recommended_models = []
        
        # Prioritize OCR models
        if ocr_models:
            recommended_models.extend(ocr_models[:3])
        
        # Then select common vision models
        common_vision_models = [
            'Qwen/Qwen2-VL-7B-Instruct',
            'Qwen/Qwen2-VL-2B-Instruct', 
            'qwen-vl-plus',
            'qwen-vl-max'
        ]
        
        for model in common_vision_models:
            if model in [m.id for m in models.data]:
                recommended_models.append(model)
                break
        
        print(f"\nRecommended models:")
        for i, model in enumerate(recommended_models[:5], 1):
            print(f"{i}. {model}")
        
        # Test first recommended model
        if recommended_models:
            test_model = recommended_models[0]
            print(f"\nTesting model: {test_model}")
            
            # Update .env file
            update_env_file(test_model)
            
            return test_model
        else:
            print("\nNo suitable OCR model found")
            return None
            
    except Exception as e:
        print(f"\nFailed to get model list: {e}")
        return None

def update_env_file(model_name):
    """Update model configuration in .env file"""
    try:
        env_path = '.env'
        
        # Read existing content
        lines = []
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        
        # Update or add OCR_MODEL
        model_updated = False
        for i, line in enumerate(lines):
            if line.startswith('OCR_MODEL='):
                lines[i] = f'OCR_MODEL={model_name}\n'
                model_updated = True
                break
        
        if not model_updated:
            lines.append(f'OCR_MODEL={model_name}\n')
        
        # Write back to file
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"✓ Updated .env file, OCR_MODEL = {model_name}")
        
    except Exception as e:
        print(f"✗ Failed to update .env file: {e}")

if __name__ == "__main__":
    model = find_working_ocr_model()
    if model:
        print(f"\nRecommend restarting Flask server to use new model: {model}")
    else:
        print("\nPlease check API configuration or use Tesseract as backup option")