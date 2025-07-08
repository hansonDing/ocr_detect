#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建客户支付报告PDF文件用于测试OCR识别功能
"""

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import datetime
import os

def create_payment_report_pdf():
    """
    创建客户支付报告PDF文件
    """
    # 文件名
    filename = "client_payment_report_mock.pdf"
    filepath = os.path.join(os.getcwd(), filename)
    
    # 创建PDF文档
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    story = []
    
    # 获取样式
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # 居中对齐
    )
    
    # 添加标题
    title = Paragraph("Client Payment Report Mock", title_style)
    story.append(title)
    story.append(Spacer(1, 20))
    
    # 创建表格数据（根据图片中的信息）
    table_data = [
        ['FieldName', 'Value'],
        ['Customer Name', 'Wu Gang'],
        ['Customer ID', '1050843'],
        ['Transaction ID', '500007826'],
        ['Transaction Amount', '6750.00'],
        ['Payment Date', '2025-01-05'],
        ['Document Timestamp', '2025-07-08 18:50:48'],
        ['Customer Country', 'US']
    ]
    
    # 创建表格
    table = Table(table_data, colWidths=[2.5*inch, 3*inch])
    
    # 设置表格样式
    table.setStyle(TableStyle([
        # 表头样式
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        
        # 数据行样式
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        
        # 边框
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        # 行间距
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.beige, colors.lightgrey])
    ]))
    
    story.append(table)
    
    # 添加一些额外信息
    story.append(Spacer(1, 30))
    
    additional_info = Paragraph(
        "<b>Report Generated:</b> {}<br/>"
        "<b>Report Type:</b> Payment Transaction Summary<br/>"
        "<b>Currency:</b> USD<br/>"
        "<b>Status:</b> Completed".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        styles['Normal']
    )
    story.append(additional_info)
    
    # 构建PDF
    doc.build(story)
    
    print(f"PDF文件已创建: {filepath}")
    print(f"文件大小: {os.path.getsize(filepath)} bytes")
    
    return filepath

if __name__ == "__main__":
    create_payment_report_pdf()