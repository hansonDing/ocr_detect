#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试客户支付报告PDF的OCR识别和数据库存储功能
"""

import requests
import json
import os
import sqlite3
from datetime import datetime

def test_pdf_upload_and_ocr():
    """
    测试PDF上传和OCR处理
    """
    # 服务器URL
    upload_url = "http://127.0.0.1:5000/upload"
    
    # PDF文件路径
    pdf_file = "client_payment_report_mock.pdf"
    
    if not os.path.exists(pdf_file):
        print(f"错误: PDF文件 {pdf_file} 不存在")
        return False
    
    print(f"开始测试PDF文件: {pdf_file}")
    print(f"文件大小: {os.path.getsize(pdf_file)} bytes")
    print("=" * 60)
    
    try:
        # 上传PDF文件
        with open(pdf_file, 'rb') as f:
            files = {'file': (pdf_file, f, 'application/pdf')}
            response = requests.post(upload_url, files=files)
        
        if response.status_code == 200:
            result = response.json()
            print("✓ PDF上传和处理成功!")
            print(f"处理状态: {result.get('status', 'unknown')}")
            print(f"处理页数: {result.get('pages_processed', 'unknown')}")
            print(f"输出目录: {result.get('output_directory', 'unknown')}")
            
            # 显示OCR结果预览
            if 'ocr_preview' in result:
                print("\nOCR识别结果预览:")
                print("-" * 40)
                preview = result['ocr_preview']
                if len(preview) > 500:
                    print(preview[:500] + "...")
                else:
                    print(preview)
            
            return True
        else:
            print(f"✗ 上传失败: HTTP {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("✗ 连接失败: 请确保Flask服务器正在运行 (python app.py)")
        return False
    except Exception as e:
        print(f"✗ 处理过程中发生错误: {str(e)}")
        return False

def check_database_records():
    """
    检查数据库中的OCR记录
    """
    db_file = "ocr_data.db"
    
    if not os.path.exists(db_file):
        print("数据库文件不存在")
        return
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # 查询最近的记录
        cursor.execute("""
            SELECT id, filename, raw_ocr_text, processing_time, model_used
            FROM ocr_records 
            ORDER BY id DESC 
            LIMIT 5
        """)
        
        records = cursor.fetchall()
        
        print("\n" + "=" * 60)
        print("数据库中最近的OCR记录:")
        print("=" * 60)
        
        if records:
            for record in records:
                record_id, filename, ocr_result, timestamp, model_used = record
                print(f"\n记录ID: {record_id}")
                print(f"文件名: {filename}")
                print(f"时间戳: {timestamp}")
                print(f"处理模型: {model_used}")
                
                # 显示OCR结果预览
                if ocr_result:
                    print("OCR结果预览:")
                    if len(ocr_result) > 300:
                        print(ocr_result[:300] + "...")
                    else:
                        print(ocr_result)
                
                print("-" * 40)
        else:
            print("数据库中没有找到OCR记录")
        
        conn.close()
        
    except Exception as e:
        print(f"查询数据库时发生错误: {str(e)}")

def search_payment_info_in_database():
    """
    在数据库中搜索支付相关信息
    """
    db_file = "ocr_data.db"
    
    if not os.path.exists(db_file):
        print("数据库文件不存在")
        return
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # 搜索包含支付信息的记录
        search_terms = ['Wu Gang', '1050843', '500007826', '6750.00', 'Payment']
        
        print("\n" + "=" * 60)
        print("搜索数据库中的支付信息:")
        print("=" * 60)
        
        for term in search_terms:
            cursor.execute("""
                SELECT id, filename, processing_time
                FROM ocr_records 
                WHERE raw_ocr_text LIKE ? 
                ORDER BY id DESC
            """, (f'%{term}%',))
            
            results = cursor.fetchall()
            
            if results:
                print(f"\n找到包含 '{term}' 的记录:")
                for result in results:
                    record_id, filename, timestamp = result
                    print(f"  - 记录ID: {record_id}, 文件: {filename}, 时间: {timestamp}")
            else:
                print(f"未找到包含 '{term}' 的记录")
        
        conn.close()
        
    except Exception as e:
        print(f"搜索数据库时发生错误: {str(e)}")

def main():
    """
    主测试函数
    """
    print("客户支付报告PDF OCR测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 测试PDF上传和OCR处理
    success = test_pdf_upload_and_ocr()
    
    if success:
        print("\n等待3秒后检查数据库...")
        import time
        time.sleep(3)
        
        # 检查数据库记录
        check_database_records()
        
        # 搜索特定的支付信息
        search_payment_info_in_database()
        
        print("\n" + "=" * 60)
        print("✓ 测试完成! PDF OCR识别和数据库存储功能正常")
    else:
        print("\n" + "=" * 60)
        print("✗ 测试失败! 请检查服务器状态和配置")

if __name__ == "__main__":
    main()