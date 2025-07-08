#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量处理OCR结果文件脚本
用于批量处理包含JSON格式OCR结果的文件，提取natural_text中的信息并存储到数据库
"""

import json
import os
import glob
from datetime import datetime
from database import init_database, extract_key_information, save_to_database

def parse_single_ocr_file(file_path: str) -> bool:
    """
    解析单个OCR结果文件
    
    Args:
        file_path: OCR结果文件路径
        
    Returns:
        bool: 是否成功处理
    """
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
            print(f"[跳过] {file_path}: 未找到OCR结果JSON数据")
            return False
        
        if processing_status != 'Success':
            print(f"[跳过] {file_path}: OCR处理状态不是成功 ({processing_status})")
            return False
        
        # 解析JSON数据
        try:
            ocr_data = json.loads(ocr_result_json)
            natural_text = ocr_data.get('natural_text', '')
            
            if not natural_text:
                print(f"[跳过] {file_path}: natural_text为空")
                return False
            
            # 使用现有的extract_key_information函数提取信息
            extracted_info = extract_key_information(natural_text)
            
            # 检查是否提取到有效信息
            if not any(extracted_info.values()):
                print(f"[警告] {file_path}: 未能提取到任何有效信息")
                # 仍然保存原始OCR文本
            
            # 保存到数据库
            filename = original_filename or os.path.basename(file_path)
            
            record_id = save_to_database(
                filename=filename,
                file_path=file_path,
                ocr_text=natural_text,
                model_used=model_used or 'OCR API',
                extracted_info=extracted_info
            )
            
            print(f"[成功] {file_path} -> 记录ID: {record_id}")
            
            # 显示提取的关键信息
            key_info = []
            if extracted_info.get('customer_name'):
                key_info.append(f"客户: {extracted_info['customer_name']}")
            if extracted_info.get('transaction_amount'):
                key_info.append(f"金额: {extracted_info['transaction_amount']}")
            if extracted_info.get('transaction_id'):
                key_info.append(f"交易ID: {extracted_info['transaction_id']}")
            
            if key_info:
                print(f"        提取信息: {', '.join(key_info)}")
            
            return True
            
        except json.JSONDecodeError as e:
            print(f"[错误] {file_path}: JSON解析错误 - {e}")
            return False
            
    except Exception as e:
        print(f"[错误] {file_path}: 处理文件时发生错误 - {e}")
        return False

def find_ocr_result_files(directory: str = '.') -> list:
    """
    查找目录中的OCR结果文件
    
    Args:
        directory: 搜索目录
        
    Returns:
        list: OCR结果文件路径列表
    """
    ocr_files = []
    
    # 查找.txt文件
    txt_files = glob.glob(os.path.join(directory, '*.txt'))
    
    for file_path in txt_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # 检查是否包含OCR结果的特征
                if ('Recognition Time:' in content and 
                    'Recognition Model:' in content and 
                    'natural_text' in content):
                    ocr_files.append(file_path)
        except:
            continue
    
    return ocr_files

def batch_process_directory(directory: str = '.') -> dict:
    """
    批量处理目录中的OCR结果文件
    
    Args:
        directory: 处理目录
        
    Returns:
        dict: 处理结果统计
    """
    print(f"正在搜索目录: {os.path.abspath(directory)}")
    
    ocr_files = find_ocr_result_files(directory)
    
    if not ocr_files:
        print("未找到OCR结果文件")
        return {'total': 0, 'success': 0, 'failed': 0}
    
    print(f"找到 {len(ocr_files)} 个OCR结果文件")
    print("="*60)
    
    success_count = 0
    failed_count = 0
    
    for file_path in ocr_files:
        if parse_single_ocr_file(file_path):
            success_count += 1
        else:
            failed_count += 1
    
    print("="*60)
    print(f"处理完成: 总计 {len(ocr_files)} 个文件")
    print(f"成功: {success_count} 个")
    print(f"失败: {failed_count} 个")
    
    return {
        'total': len(ocr_files),
        'success': success_count,
        'failed': failed_count
    }

def main():
    """
    主函数
    """
    print("OCR结果批量处理工具")
    print("="*60)
    
    # 初始化数据库
    init_database()
    
    # 获取用户输入
    print("请选择处理模式:")
    print("1. 处理当前目录中的所有OCR结果文件")
    print("2. 处理指定文件")
    print("3. 处理指定目录")
    
    choice = input("请输入选择 (1-3): ").strip()
    
    if choice == '1':
        # 处理当前目录
        batch_process_directory('.')
        
    elif choice == '2':
        # 处理指定文件
        file_path = input("请输入文件路径: ").strip()
        if os.path.exists(file_path):
            print(f"正在处理文件: {file_path}")
            print("="*60)
            if parse_single_ocr_file(file_path):
                print("文件处理成功")
            else:
                print("文件处理失败")
        else:
            print("文件不存在")
            
    elif choice == '3':
        # 处理指定目录
        directory = input("请输入目录路径: ").strip()
        if os.path.exists(directory) and os.path.isdir(directory):
            batch_process_directory(directory)
        else:
            print("目录不存在")
            
    else:
        print("无效选择")

if __name__ == '__main__':
    main()