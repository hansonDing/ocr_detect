#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite database query example script

This script demonstrates how to query records in the OCR database
Usage: python query_database.py
"""

import sqlite3
import os
import pandas as pd
from datetime import datetime, timedelta
from database import get_all_records, search_records

# Database file path
DB_PATH = os.path.join(os.path.dirname(__file__), 'ocr_data.db')

def check_database_exists():
    """Check if database exists"""
    if not os.path.exists(DB_PATH):
        print(f"❌ Database file does not exist: {DB_PATH}")
        print("Please run the OCR application first to generate some data")
        return False
    return True

def get_database_info():
    """Get basic database information"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get total record count
    cursor.execute("SELECT COUNT(*) FROM ocr_records")
    total_records = cursor.fetchone()[0]
    
    # Get latest record time
    cursor.execute("SELECT MAX(processing_time) FROM ocr_records")
    latest_time = cursor.fetchone()[0]
    
    # Get earliest record time
    cursor.execute("SELECT MIN(processing_time) FROM ocr_records")
    earliest_time = cursor.fetchone()[0]
    
    # Get statistics for different models
    cursor.execute("SELECT model_used, COUNT(*) FROM ocr_records GROUP BY model_used")
    model_stats = cursor.fetchall()
    
    conn.close()
    
    print("📊 Database Information Overview")
    print("=" * 50)
    print(f"Database Path: {DB_PATH}")
    print(f"Total Records: {total_records}")
    print(f"Earliest Record: {earliest_time}")
    print(f"Latest Record: {latest_time}")
    print("\n🤖 Model Usage Statistics:")
    for model, count in model_stats:
        print(f"  {model}: {count} records")
    print()

def query_recent_records(days=7):
    """Query records from recent days"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Calculate date
    since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    cursor.execute("""
        SELECT id, filename, customer_name, transaction_amount, processing_time
        FROM ocr_records 
        WHERE processing_time >= ?
        ORDER BY processing_time DESC
    """, (since_date,))
    
    records = cursor.fetchall()
    conn.close()
    
    print(f"📅 Records from the last {days} days ({len(records)} records)")
    print("=" * 50)
    if records:
        print(f"{'ID':<5} {'Filename':<20} {'Customer':<15} {'Amount':<15} {'Processing Time':<20}")
        print("-" * 80)
        for record in records:
            record_id, filename, customer_name, amount, proc_time = record
            filename = filename[:18] + '...' if len(filename) > 20 else filename
            customer_name = customer_name[:13] + '...' if customer_name and len(customer_name) > 15 else (customer_name or 'N/A')
            amount = amount[:13] + '...' if amount and len(amount) > 15 else (amount or 'N/A')
            print(f"{record_id:<5} {filename:<20} {customer_name:<15} {amount:<15} {proc_time:<20}")
    else:
        print("No records found")
    print()

def query_by_customer():
    """Query records by customer"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all records with customer names
    cursor.execute("""
        SELECT DISTINCT customer_name 
        FROM ocr_records 
        WHERE customer_name IS NOT NULL AND customer_name != ''
        ORDER BY customer_name
    """)
    
    customers = cursor.fetchall()
    
    if not customers:
        print("👤 No customer information found")
        print()
        conn.close()
        return
    
    print(f"👤 Customer Record Statistics ({len(customers)} customers total)")
    print("=" * 50)
    
    for customer in customers:
        customer_name = customer[0]
        cursor.execute("""
            SELECT COUNT(*), MAX(processing_time)
            FROM ocr_records 
            WHERE customer_name = ?
        """, (customer_name,))
        
        count, last_time = cursor.fetchone()
        print(f"{customer_name}: {count} records, last processed: {last_time}")
    
    conn.close()
    print()

def query_high_confidence_records():
    """Query high confidence records"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, filename, customer_name, extraction_confidence, processing_time
        FROM ocr_records 
        WHERE extraction_confidence > 0.5
        ORDER BY extraction_confidence DESC
        LIMIT 10
    """)
    
    records = cursor.fetchall()
    conn.close()
    
    print(f"🎯 High Confidence Records (confidence>0.5, showing top 10)")
    print("=" * 70)
    if records:
        print(f"{'ID':<5} {'Filename':<20} {'Customer':<15} {'Confidence':<10} {'Processing Time':<20}")
        print("-" * 70)
        for record in records:
            record_id, filename, customer_name, confidence, proc_time = record
            filename = filename[:18] + '...' if len(filename) > 20 else filename
            customer_name = customer_name[:13] + '...' if customer_name and len(customer_name) > 15 else (customer_name or 'N/A')
            print(f"{record_id:<5} {filename:<20} {customer_name:<15} {confidence:<10.2f} {proc_time:<20}")
    else:
        print("No high confidence records found")
    print()

def search_by_keyword():
    """Search by keyword"""
    keyword = input("Please enter search keyword: ").strip()
    if not keyword:
        print("❌ Keyword cannot be empty")
        return
    
    # Use existing search function
    results = search_records(keyword=keyword)
    
    print(f"🔍 Search Results: '{keyword}' (found {len(results)} records)")
    print("=" * 60)
    
    if results:
        for i, record in enumerate(results[:5], 1):  # Only show first 5
            print(f"\n📄 Record {i} (ID: {record['id']})")
            print(f"Filename: {record['filename']}")
            print(f"Customer: {record['customer_name'] or 'N/A'}")
            print(f"Transaction ID: {record['transaction_id'] or 'N/A'}")
            print(f"Amount: {record['transaction_amount'] or 'N/A'}")
            print(f"Processing Time: {record['processing_time']}")
            print(f"Model: {record['model_used']}")
            print(f"Confidence: {record['extraction_confidence']:.2f}")
        
        if len(results) > 5:
            print(f"\n... {len(results) - 5} more records not displayed")
    else:
        print("No matching records found")
    print()

def export_to_csv():
    """Export data to CSV file"""
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM ocr_records ORDER BY processing_time DESC", conn)
        conn.close()
        
        if len(df) == 0:
            print("❌ No data to export")
            return
        
        filename = f"ocr_records_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"✅ Data exported to: {filename}")
        print(f"Total {len(df)} records exported")
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
    print()

def interactive_query():
    """Interactive query menu"""
    while True:
        print("\n🔧 SQLite Database Query Tool")
        print("=" * 30)
        print("1. View database information")
        print("2. View recent records")
        print("3. Query by customer")
        print("4. View high confidence records")
        print("5. Keyword search")
        print("6. Export to CSV")
        print("7. Custom SQL query")
        print("0. Exit")
        
        choice = input("\nPlease select operation (0-7): ").strip()
        
        if choice == '0':
            print("👋 Goodbye!")
            break
        elif choice == '1':
            get_database_info()
        elif choice == '2':
            days = input("View records from how many days ago (default 7 days): ").strip()
            days = int(days) if days.isdigit() else 7
            query_recent_records(days)
        elif choice == '3':
            query_by_customer()
        elif choice == '4':
            query_high_confidence_records()
        elif choice == '5':
            search_by_keyword()
        elif choice == '6':
            export_to_csv()
        elif choice == '7':
            custom_sql_query()
        else:
            print("❌ Invalid selection, please try again")

def custom_sql_query():
    """Custom SQL query"""
    print("\n📝 Custom SQL Query")
    print("Hint: Table name is 'ocr_records'")
    print("Enter 'help' to view table structure, enter 'exit' to return to main menu")
    
    while True:
        sql = input("\nSQL> ").strip()
        
        if sql.lower() == 'exit':
            break
        elif sql.lower() == 'help':
            print("\nTable Structure:")
            print("id, filename, file_path, processing_time, customer_name,")
            print("customer_id, transaction_id, transaction_amount, payment_date,")
            print("document_timestamp, customer_country, raw_ocr_text, model_used, extraction_confidence")
            continue
        elif not sql:
            continue
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(sql)
            
            if sql.lower().startswith('select'):
                results = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                
                if results:
                    print(f"\nQuery Results ({len(results)} rows):")
                    print(" | ".join(columns))
                    print("-" * (len(" | ".join(columns))))
                    for row in results[:10]:  # Only show first 10 rows
                        print(" | ".join(str(cell) for cell in row))
                    if len(results) > 10:
                        print(f"... {len(results) - 10} more rows not displayed")
                else:
                    print("Query result is empty")
            else:
                conn.commit()
                print(f"✅ Query executed successfully, {cursor.rowcount} rows affected")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ SQL execution error: {e}")

def main():
    """Main function"""
    print("🗄️ OCR Database Query Tool")
    print("=" * 40)
    
    if not check_database_exists():
        return
    
    # Display basic information
    get_database_info()
    
    # Start interactive query
    interactive_query()

if __name__ == '__main__':
    main()