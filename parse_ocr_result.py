#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR结果解析和数据库存储脚本
用于解析OCR识别结果文件中的JSON格式数据，提取natural_text中的表格信息并存储到数据库
"""

import json
import re
import os
from datetime import datetime
from database import init_database, extract_key_information, save_to_database

def parse_ocr_result_file(file_path: str):
    """
    解析OCR结果文件
    
    Args:
        file_path: OCR结果文件路径
    """
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析文件内容
        lines = content.strip().split('\n')
        
        # 提取基本信息
        recognition_time = None
        original_filename = None
        model_used = None
        processing_status = None
        ocr_result_json = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('Recognition Time:'):
                recognition_time = line.replace('Recognition Time:', '').strip()
            elif line.startswith('Original Filename:'):
                original_filename = line.replace('Original Filename:', '').strip()
            elif line.startswith('Recognition Model:'):
                model_used = line.replace('Recognition Model:', '').strip()
            elif line.startswith('Processing Status:'):
                processing_status = line.replace('Processing Status:', '').strip()
            elif line.startswith('{') and 'natural_text' in line:
                # 这是JSON结果行
                ocr_result_json = line
        
        if not ocr_result_json:
            print("未找到OCR结果JSON数据")
            return
        
        if processing_status != 'Success':
            print(f"OCR处理状态不是成功: {processing_status}")
            return
        
        # 解析JSON数据
        try:
            ocr_data = json.loads(ocr_result_json)
            natural_text = ocr_data.get('natural_text', '')
            
            if not natural_text:
                print("natural_text为空")
                return
            
            print(f"原始natural_text内容:")
            print(natural_text)
            print("\n" + "="*50 + "\n")
            
            # 使用现有的extract_key_information函数提取信息
            extracted_info = extract_key_information(natural_text)
            
            print("提取的信息:")
            for key, value in extracted_info.items():
                print(f"{key}: {value}")
            
            # 检查是否提取到有效信息
            if not any(extracted_info.values()):
                print("警告: 未能提取到任何有效信息")
                return
            
            # 保存到数据库
            filename = original_filename or os.path.basename(file_path)
            file_path_for_db = file_path
            
            record_id = save_to_database(
                filename=filename,
                file_path=file_path_for_db,
                ocr_text=natural_text,
                model_used=model_used or 'OCR API',
                extracted_info=extracted_info
            )
            
            print(f"\n数据已成功保存到数据库，记录ID: {record_id}")
            
            # 显示保存的信息摘要
            print("\n保存的信息摘要:")
            print(f"- 文件名: {filename}")
            print(f"- 客户姓名: {extracted_info.get('customer_name', 'N/A')}")
            print(f"- 客户ID: {extracted_info.get('customer_id', 'N/A')}")
            print(f"- 交易ID: {extracted_info.get('transaction_id', 'N/A')}")
            print(f"- 交易金额: {extracted_info.get('transaction_amount', 'N/A')}")
            print(f"- 支付日期: {extracted_info.get('payment_date', 'N/A')}")
            print(f"- 客户国家: {extracted_info.get('customer_country', 'N/A')}")
            
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            print(f"问题行: {ocr_result_json}")
            return
            
    except Exception as e:
        print(f"处理文件时发生错误: {e}")
        return

def main():
    """
    主函数
    """
    # 初始化数据库
    init_database()
    
    # 默认处理ocr_test.txt文件
    default_file = "ocr_test.txt"
    
    if os.path.exists(default_file):
        print(f"正在处理文件: {default_file}")
        print("="*60)
        parse_ocr_result_file(default_file)
    else:
        print(f"默认文件 {default_file} 不存在")
        
        # 让用户输入文件路径
        file_path = input("请输入OCR结果文件路径: ").strip()
        if file_path and os.path.exists(file_path):
            print(f"正在处理文件: {file_path}")
            print("="*60)
            parse_ocr_result_file(file_path)
        else:
            print("文件路径无效或文件不存在")

if __name__ == '__main__':
    main()