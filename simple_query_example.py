#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple SQLite database query example
Demonstrates basic operations for querying OCR records database
"""

import sqlite3
import os
from datetime import datetime

def connect_database():
    """Connect to SQLite database"""
    db_path = 'ocr_data.db'
    if not os.path.exists(db_path):
        print(f"❌ Database file does not exist: {db_path}")
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Make results accessible by column name
        return conn
    except sqlite3.Error as e:
        print(f"❌ Failed to connect to database: {e}")
        return None

def show_table_structure():
    """Show database table structure"""
    conn = connect_database()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(ocr_records)")
        columns = cursor.fetchall()
        
        print("\n📋 Database table structure (ocr_records):")
        print("-" * 60)
        for col in columns:
            print(f"{col['name']:20} {col['type']:15} {'NOT NULL' if col['notnull'] else 'NULL'}")
        
    except sqlite3.Error as e:
        print(f"❌ Failed to query table structure: {e}")
    finally:
        conn.close()

def count_records():
    """Count total records"""
    conn = connect_database()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM ocr_records")
        result = cursor.fetchone()
        print(f"\n📊 Database contains {result['total']} records in total")
        
    except sqlite3.Error as e:
        print(f"❌ Failed to count records: {e}")
    finally:
        conn.close()

def show_all_records():
    """Show all records"""
    conn = connect_database()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, filename, customer_name, transaction_amount, 
                   model_used, processing_time
            FROM ocr_records 
            ORDER BY processing_time DESC
        """)
        records = cursor.fetchall()
        
        if not records:
            print("\n📝 No records in database")
            return
        
        print("\n📋 All OCR records:")
        print("-" * 80)
        print(f"{'ID':<4} {'Filename':<20} {'Customer':<15} {'Amount':<12} {'Model':<10} {'Time':<19}")
        print("-" * 80)
        
        for record in records:
            print(f"{record['id']:<4} {record['filename']:<20} "
                  f"{record['customer_name'] or 'N/A':<15} "
                  f"{record['transaction_amount'] or 'N/A':<12} "
                  f"{record['model_used']:<10} "
                  f"{record['processing_time']:<19}")
        
    except sqlite3.Error as e:
        print(f"❌ Failed to query records: {e}")
    finally:
        conn.close()

def search_by_keyword(keyword):
    """Search by keyword"""
    conn = connect_database()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, filename, customer_name, transaction_amount, raw_ocr_text
            FROM ocr_records 
            WHERE raw_ocr_text LIKE ? OR filename LIKE ?
            ORDER BY processing_time DESC
        """, (f'%{keyword}%', f'%{keyword}%'))
        records = cursor.fetchall()
        
        if not records:
            print(f"\n🔍 No records found containing keyword '{keyword}'")
            return
        
        print(f"\n🔍 Records containing keyword '{keyword}':")
        print("-" * 60)
        
        for record in records:
            print(f"ID: {record['id']}")
            print(f"Filename: {record['filename']}")
            print(f"Customer: {record['customer_name'] or 'N/A'}")
            print(f"Amount: {record['transaction_amount'] or 'N/A'}")
            print(f"OCR Text: {record['raw_ocr_text'][:100]}...")
            print("-" * 60)
        
    except sqlite3.Error as e:
        print(f"❌ Search failed: {e}")
    finally:
        conn.close()

def get_record_by_id(record_id):
    """Get specific record by ID"""
    conn = connect_database()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM ocr_records WHERE id = ?
        """, (record_id,))
        record = cursor.fetchone()
        
        if not record:
            print(f"\n❌ No record found with ID {record_id}")
            return
        
        print(f"\n📄 Record details (ID: {record_id}):")
        print("=" * 50)
        print(f"Filename: {record['filename']}")
        print(f"Customer Name: {record['customer_name'] or 'N/A'}")
        print(f"Customer ID: {record['customer_id'] or 'N/A'}")
        print(f"Transaction ID: {record['transaction_id'] or 'N/A'}")
        print(f"Transaction Amount: {record['transaction_amount'] or 'N/A'}")
        print(f"Payment Date: {record['payment_date'] or 'N/A'}")
        print(f"Document Timestamp: {record['document_timestamp'] or 'N/A'}")
        print(f"Customer Country: {record['customer_country'] or 'N/A'}")
        print(f"OCR Model: {record['model_used']}")
        print(f"Creation Time: {record['processing_time']}")
        print(f"\nOCR Text:\n{record['raw_ocr_text']}")
        
    except sqlite3.Error as e:
        print(f"❌ Failed to query record: {e}")
    finally:
        conn.close()

def main():
    """Main function - demonstrate various query operations"""
    print("🔍 SQLite Database Query Example")
    print("=" * 40)
    
    # 1. Show table structure
    show_table_structure()
    
    # 2. Count records
    count_records()
    
    # 3. Show all records
    show_all_records()
    
    # 4. Search example
    print("\n" + "=" * 40)
    print("🔍 Search Example:")
    search_by_keyword("test")
    
    # 5. Get specific record
    print("\n" + "=" * 40)
    print("📄 Get Specific Record Example:")
    get_record_by_id(1)
    
    print("\n✅ Query example completed!")

if __name__ == "__main__":
    main()