#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试JSON格式OCR结果API端点
"""

import requests
import json

def test_json_ocr_api():
    """
    测试JSON格式OCR结果处理API
    """
    # API端点
    api_url = "http://127.0.0.1:5000/api/process-json-ocr"
    
    # 测试数据1: 直接JSON结果
    test_json_data = {
        "json_result": '{"primary_language":"en","is_rotation_valid":true,"rotation_correction":0,"is_table":true,"is_diagram":false,"natural_text":"| Field Name       | Value                  |\\n|------------------|------------------------|\\n| Customer Name    | Zhang Wei              |\\n| Customer ID      | 1058901                |\\n| Transaction ID   | 5000067890             |\\n| Transaction Amount | 8888.88              |\\n| Payment Date     | 2025-01-15             |\\n| Document Timestamp | 2025-01-15 14:30:25   |\\n| Customer Country | CN                     |"}',
        "filename": "test_api_document.pdf",
        "file_path": "/test/path/test_api_document.pdf",
        "model_used": "OCR API Test"
    }
    
    print("测试1: 处理JSON格式OCR结果")
    print("="*50)
    
    try:
        response = requests.post(api_url, json=test_json_data)
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print("✓ API调用成功")
                print(f"记录ID: {result['record_id']}")
                print("提取的信息:")
                for key, value in result['extracted_info'].items():
                    if value:
                        print(f"  {key}: {value}")
                print("\n格式化信息:")
                print(result['formatted_info'])
            else:
                print(f"✗ 处理失败: {result['message']}")
        else:
            print(f"✗ HTTP错误: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"✗ 请求异常: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 测试数据2: 完整OCR结果文本
    test_ocr_text_data = {
        "ocr_text": """Recognition Time: 2025-01-15T16:45:30.123456
Original Filename: invoice_sample.pdf - Page 1
Recognition Model: Advanced OCR API
Processing Status: Success

Recognition Result:
{"primary_language":"en","is_rotation_valid":true,"rotation_correction":0,"is_table":true,"is_diagram":false,"natural_text":"| Field Name       | Value                  |\\n|------------------|------------------------|\\n| Customer Name    | Li Ming                |\\n| Customer ID      | 1059876                |\\n| Transaction ID   | 5000098765             |\\n| Transaction Amount | 12345.67             |\\n| Payment Date     | 2025-01-20             |\\n| Document Timestamp | 2025-01-20 09:15:40   |\\n| Customer Country | SG                     |"}""",
        "filename": "invoice_sample.pdf",
        "file_path": "/test/path/invoice_sample.pdf"
    }
    
    print("测试2: 处理完整OCR结果文本")
    print("="*50)
    
    try:
        response = requests.post(api_url, json=test_ocr_text_data)
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print("✓ API调用成功")
                print(f"记录ID: {result['record_id']}")
                print("提取的信息:")
                for key, value in result['extracted_info'].items():
                    if value:
                        print(f"  {key}: {value}")
                print("\n格式化信息:")
                print(result['formatted_info'])
            else:
                print(f"✗ 处理失败: {result['message']}")
        else:
            print(f"✗ HTTP错误: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"✗ 请求异常: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 测试数据3: 错误情况 - 缺少必要参数
    test_error_data = {
        "filename": "error_test.pdf"
        # 缺少json_result和ocr_text
    }
    
    print("测试3: 错误处理 - 缺少必要参数")
    print("="*50)
    
    try:
        response = requests.post(api_url, json=test_error_data)
        
        if response.status_code == 400:
            result = response.json()
            print(f"✓ 正确返回错误: {result['message']}")
        else:
            print(f"✗ 未预期的响应: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"✗ 请求异常: {e}")

def test_database_records():
    """
    测试获取数据库记录
    """
    print("\n测试: 获取最新数据库记录")
    print("="*50)
    
    try:
        response = requests.get("http://127.0.0.1:5000/database/records")
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                records = result['records']
                print(f"✓ 获取到 {len(records)} 条记录")
                
                # 显示最新的3条记录
                for i, record in enumerate(records[:3]):
                    print(f"\n记录 {i+1}:")
                    print(f"  ID: {record.get('id')}")
                    print(f"  文件名: {record.get('filename')}")
                    print(f"  客户姓名: {record.get('customer_name')}")
                    print(f"  交易金额: {record.get('transaction_amount')}")
                    print(f"  处理时间: {record.get('processing_time')}")
            else:
                print(f"✗ 获取失败: {result['message']}")
        else:
            print(f"✗ HTTP错误: {response.status_code}")
            
    except Exception as e:
        print(f"✗ 请求异常: {e}")

def main():
    """
    主测试函数
    """
    print("JSON格式OCR结果API测试")
    print("="*60)
    
    # 检查服务器是否运行
    try:
        response = requests.get("http://127.0.0.1:5000/")
        if response.status_code == 200:
            print("✓ OCR服务器正在运行")
        else:
            print("✗ OCR服务器响应异常")
            return
    except:
        print("✗ 无法连接到OCR服务器，请确保服务器正在运行")
        return
    
    print("\n开始API测试...\n")
    
    # 运行测试
    test_json_ocr_api()
    test_database_records()
    
    print("\n测试完成!")

if __name__ == '__main__':
    main()