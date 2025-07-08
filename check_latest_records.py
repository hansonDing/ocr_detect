#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check latest records in database
"""

import sqlite3
import os

def check_latest_records():
    """Check latest database records"""
    db_path = 'ocr_data.db'
    
    if not os.path.exists(db_path):
        print("Database file does not exist")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get latest 3 records
        cursor.execute('''
            SELECT id, filename, customer_name, customer_id, transaction_id, 
                   transaction_amount, payment_date, document_timestamp, 
                   customer_country, extraction_confidence, processing_time
            FROM ocr_records 
            ORDER BY id DESC 
            LIMIT 3
        ''')
        
        records = cursor.fetchall()
        
        print("Latest 3 records:")
        print("=" * 80)
        
        for record in records:
            print(f"ID: {record[0]}")
            print(f"Filename: {record[1]}")
            print(f"Customer Name: {record[2]}")
            print(f"Customer ID: {record[3]}")
            print(f"Transaction ID: {record[4]}")
            print(f"Transaction Amount: {record[5]}")
            print(f"Payment Date: {record[6]}")
            print(f"Document Timestamp: {record[7]}")
            print(f"Customer Country: {record[8]}")
            print(f"Extraction Confidence: {record[9]}")
            print(f"Processing Time: {record[10]}")
            print("-" * 40)
        
        conn.close()
        
    except Exception as e:
        print(f"Error occurred while querying database: {e}")

if __name__ == "__main__":
    check_latest_records()