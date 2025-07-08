#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON格式OCR结果处理器
用于处理包含natural_text的JSON格式OCR结果
"""

import json
from typing import Dict, Optional, Tuple
from database import extract_key_information, save_to_database

def process_json_ocr_result(json_str: str, filename: str = None, file_path: str = None, model_used: str = 'OCR API') -> Tuple[bool, Optional[int], Dict]:
    """
    处理JSON格式的OCR结果
    
    Args:
        json_str: JSON格式的OCR结果字符串
        filename: 原始文件名
        file_path: 文件路径
        model_used: 使用的OCR模型
        
    Returns:
        Tuple[bool, Optional[int], Dict]: (是否成功, 记录ID, 提取的信息)
    """
    try:
        # 解析JSON数据
        ocr_data = json.loads(json_str)
        
        # 获取natural_text
        natural_text = ocr_data.get('natural_text', '')
        
        if not natural_text:
            return False, None, {'error': 'natural_text为空'}
        
        # 提取关键信息
        extracted_info = extract_key_information(natural_text)
        
        # 保存到数据库
        record_id = save_to_database(
            filename=filename or 'unknown',
            file_path=file_path or '',
            ocr_text=natural_text,
            model_used=model_used,
            extracted_info=extracted_info
        )
        
        return True, record_id, extracted_info
        
    except json.JSONDecodeError as e:
        return False, None, {'error': f'JSON解析错误: {e}'}
    except Exception as e:
        return False, None, {'error': f'处理错误: {e}'}

def process_ocr_result_text(ocr_result_text: str, filename: str = None, file_path: str = None) -> Tuple[bool, Optional[int], Dict]:
    """
    处理OCR结果文本（包含完整的识别信息）
    
    Args:
        ocr_result_text: 完整的OCR结果文本
        filename: 原始文件名
        file_path: 文件路径
        
    Returns:
        Tuple[bool, Optional[int], Dict]: (是否成功, 记录ID, 提取的信息)
    """
    try:
        lines = ocr_result_text.strip().split('\n')
        
        # 提取基本信息
        recognition_time = None
        original_filename = filename
        model_used = 'OCR API'
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
                ocr_result_json = line
        
        if not ocr_result_json:
            return False, None, {'error': '未找到OCR结果JSON数据'}
        
        if processing_status and processing_status != 'Success':
            return False, None, {'error': f'OCR处理状态不是成功: {processing_status}'}
        
        # 使用JSON处理函数
        return process_json_ocr_result(
            json_str=ocr_result_json,
            filename=original_filename,
            file_path=file_path,
            model_used=model_used
        )
        
    except Exception as e:
        return False, None, {'error': f'文本解析错误: {e}'}

def extract_natural_text_from_json(json_str: str) -> Optional[str]:
    """
    从JSON字符串中提取natural_text
    
    Args:
        json_str: JSON格式的OCR结果字符串
        
    Returns:
        Optional[str]: 提取的natural_text，如果失败返回None
    """
    try:
        ocr_data = json.loads(json_str)
        return ocr_data.get('natural_text')
    except:
        return None

def format_extracted_info(extracted_info: Dict) -> str:
    """
    格式化提取的信息为可读字符串
    
    Args:
        extracted_info: 提取的信息字典
        
    Returns:
        str: 格式化的信息字符串
    """
    info_lines = []
    
    field_names = {
        'customer_name': '客户姓名',
        'customer_id': '客户ID',
        'transaction_id': '交易ID',
        'transaction_amount': '交易金额',
        'payment_date': '支付日期',
        'document_timestamp': '文档时间戳',
        'customer_country': '客户国家'
    }
    
    for key, value in extracted_info.items():
        if value and key in field_names:
            info_lines.append(f"{field_names[key]}: {value}")
    
    return '\n'.join(info_lines) if info_lines else '未提取到有效信息'

# 示例用法
if __name__ == '__main__':
    # 测试JSON处理
    test_json = '{"primary_language":"en","is_rotation_valid":true,"rotation_correction":0,"is_table":true,"is_diagram":false,"natural_text":"| Field Name       | Value                  |\\n|------------------|------------------------|\\n| Customer Name    | Sun Hong               |\\n| Customer ID      | 1057805                |\\n| Transaction ID   | 5000056583             |\\n| Transaction Amount | 6651.00              |\\n| Payment Date     | 2025-11-21             |\\n| Document Timestamp | 2025-07-08 18:50:52   |\\n| Customer Country | HK                     |"}'
    
    success, record_id, info = process_json_ocr_result(
        json_str=test_json,
        filename='test_document.pdf',
        file_path='/path/to/test_document.pdf'
    )
    
    if success:
        print(f"处理成功，记录ID: {record_id}")
        print("提取的信息:")
        print(format_extracted_info(info))
    else:
        print(f"处理失败: {info.get('error', '未知错误')}")