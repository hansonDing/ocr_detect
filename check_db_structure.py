#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check database table structure
"""

import sqlite3

def check_database_structure():
    """Check database table structure"""
    try:
        conn = sqlite3.connect('ocr_data.db')
        cursor = conn.cursor()
        
        # Get table structure
        cursor.execute("PRAGMA table_info(ocr_records)")
        columns = cursor.fetchall()
        
        print("📋 Database table structure (ocr_records):")
        print("-" * 60)
        print(f"{'Column Name':<20} {'Type':<15} {'Not Null':<8} {'Default':<10}")
        print("-" * 60)
        
        for col in columns:
            cid, name, type_name, notnull, default_value, pk = col
            print(f"{name:<20} {type_name:<15} {'Yes' if notnull else 'No':<8} {default_value or 'NULL':<10}")
        
        # View all fields of one record
        cursor.execute("SELECT * FROM ocr_records LIMIT 1")
        record = cursor.fetchone()
        
        if record:
            print("\n📄 Sample record field values:")
            print("-" * 60)
            for i, col in enumerate(columns):
                col_name = col[1]
                value = record[i] if i < len(record) else 'N/A'
                print(f"{col_name}: {value}")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Other error: {e}")

if __name__ == "__main__":
    check_database_structure()