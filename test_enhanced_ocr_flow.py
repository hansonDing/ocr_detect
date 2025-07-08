#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试增强的OCR处理流程
验证前端提交PDF文件后，OCR识别结果能够自动处理JSON格式并存入数据库
"""

import os
import json
import requests
import time
from datetime import datetime

def test_pdf_upload_and_processing():
    """
    测试PDF文件上传和OCR处理流程
    """
    print("=" * 60)
    print("测试PDF文件上传和OCR处理流程")
    print("=" * 60)
    
    # 测试文件路径
    test_pdf = "client_payment_report_mock.pdf"
    
    if not os.path.exists(test_pdf):
        print(f"测试文件不存在: {test_pdf}")
        return False
    
    # 上传文件到服务器
    url = "http://localhost:5000/upload"
    
    try:
        with open(test_pdf, 'rb') as f:
            files = {'file': (test_pdf, f, 'application/pdf')}
            data = {'output_format': 'txt'}  # 使用txt格式以便生成JSON结构
            
            print(f"上传文件: {test_pdf}")
            response = requests.post(url, files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"上传成功: {result.get('success')}")
                print(f"消息: {result.get('message')}")
                
                if result.get('success'):
                    print(f"文件类型: {result.get('file_type')}")
                    print(f"输出格式: {result.get('output_format')}")
                    print(f"记录ID: {result.get('record_id')}")
                    print(f"提取字段数: {result.get('extracted_fields_count')}")
                    
                    if result.get('extracted_info'):
                        print("\n提取的信息:")
                        for key, value in result.get('extracted_info', {}).items():
                            if value:
                                print(f"  {key}: {value}")
                    
                    return True
                else:
                    print(f"处理失败: {result.get('message')}")
                    return False
            else:
                print(f"HTTP错误: {response.status_code}")
                print(f"响应内容: {response.text}")
                return False
                
    except Exception as e:
        print(f"测试失败: {str(e)}")
        return False

def test_image_upload_with_json_response():
    """
    测试图片上传，模拟JSON格式的OCR响应
    """
    print("\n" + "=" * 60)
    print("测试图片上传和JSON格式OCR响应处理")
    print("=" * 60)
    
    # 查找测试图片文件
    test_images = []
    for ext in ['*.png', '*.jpg', '*.jpeg']:
        import glob
        test_images.extend(glob.glob(f"uploads/{ext}"))
    
    if not test_images:
        print("未找到测试图片文件")
        return False
    
    test_image = test_images[0]
    print(f"使用测试图片: {test_image}")
    
    url = "http://localhost:5000/upload"
    
    try:
        with open(test_image, 'rb') as f:
            files = {'file': (os.path.basename(test_image), f, 'image/jpeg')}
            data = {
                'output_format': 'txt',
                'image_type': 'table'
            }
            
            print(f"上传图片: {test_image}")
            response = requests.post(url, files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"上传成功: {result.get('success')}")
                print(f"消息: {result.get('message')}")
                
                if result.get('success'):
                    print(f"文件类型: {result.get('file_type')}")
                    print(f"模型信息: {result.get('model_info')}")
                    print(f"记录ID: {result.get('record_id')}")
                    print(f"提取字段数: {result.get('extracted_fields_count')}")
                    
                    if result.get('extracted_info'):
                        print("\n提取的信息:")
                        for key, value in result.get('extracted_info', {}).items():
                            if value:
                                print(f"  {key}: {value}")
                    
                    return True
                else:
                    print(f"处理失败: {result.get('message')}")
                    return False
            else:
                print(f"HTTP错误: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"测试失败: {str(e)}")
        return False

def test_database_records():
    """
    测试数据库记录查询
    """
    print("\n" + "=" * 60)
    print("查询数据库记录")
    print("=" * 60)
    
    try:
        url = "http://localhost:5000/database/records"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            records = data.get('records', [])
            
            print(f"数据库中共有 {len(records)} 条记录")
            
            if records:
                print("\n最新的3条记录:")
                for i, record in enumerate(records[:3]):
                    print(f"\n记录 {i+1}:")
                    print(f"  ID: {record.get('id')}")
                    print(f"  文件名: {record.get('filename')}")
                    print(f"  客户姓名: {record.get('customer_name')}")
                    print(f"  交易金额: {record.get('transaction_amount')}")
                    print(f"  OCR模型: {record.get('model_used')}")
                    print(f"  处理时间: {record.get('processing_time')}")
            
            return True
        else:
            print(f"查询失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"查询失败: {str(e)}")
        return False

def main():
    """
    主测试函数
    """
    print("增强OCR处理流程测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查服务器是否运行
    try:
        response = requests.get("http://localhost:5000/")
        if response.status_code != 200:
            print("服务器未运行，请先启动 python app.py")
            return
    except Exception:
        print("无法连接到服务器，请先启动 python app.py")
        return
    
    # 执行测试
    tests = [
        ("PDF文件上传测试", test_pdf_upload_and_processing),
        ("图片上传测试", test_image_upload_with_json_response),
        ("数据库记录查询", test_database_records)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n开始执行: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"{test_name}: {'通过' if result else '失败'}")
        except Exception as e:
            print(f"{test_name}: 异常 - {str(e)}")
            results.append((test_name, False))
        
        time.sleep(1)  # 等待1秒
    
    # 输出测试结果摘要
    print("\n" + "=" * 60)
    print("测试结果摘要")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\n总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！增强的OCR处理流程工作正常。")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查相关功能。")

if __name__ == "__main__":
    main()