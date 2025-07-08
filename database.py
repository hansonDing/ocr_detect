import sqlite3
import os
import re
from datetime import datetime
from typing import Dict, Optional, List

# Database file path
DB_PATH = os.path.join(os.path.dirname(__file__), 'ocr_data.db')

def init_database():
    """Initialize database and create table structure"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create OCR records table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ocr_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            file_path TEXT,
            processing_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            customer_name TEXT,
            customer_id TEXT,
            transaction_id TEXT,
            transaction_amount TEXT,
            payment_date TEXT,
            document_timestamp TEXT,
            customer_country TEXT,
            raw_ocr_text TEXT,
            model_used TEXT,
            extraction_confidence REAL DEFAULT 0.0
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Database initialized at: {DB_PATH}")

def extract_key_information(ocr_text: str) -> Dict[str, Optional[str]]:
    """Extract key information from OCR text"""
    # Initialize result dictionary
    extracted_info = {
        'customer_name': None,
        'customer_id': None,
        'transaction_id': None,
        'transaction_amount': None,
        'payment_date': None,
        'document_timestamp': None,
        'customer_country': None
    }
    
    # Convert to lowercase for matching
    text_lower = ocr_text.lower()
    
    # Define keyword patterns
    patterns = {
        'customer_name': [
            r'customer\s*name[:\s]*([^\n\r]+)',
            r'name[:\s]*([^\n\r]+)',
            r'customer\s*name[:\s]*([^\n\r]+)',
            r'client\s*name[:\s]*([^\n\r]+)'
        ],
        'customer_id': [
            r'customer\s*id[:\s]*([A-Za-z0-9\-_]+)',
            r'customer\s*number[:\s]*([A-Za-z0-9\-_]+)',
            r'client\s*id[:\s]*([A-Za-z0-9\-_]+)',
            r'id[:\s]*([A-Za-z0-9\-_]+)'
        ],
        'transaction_id': [
            r'transaction\s*id[:\s]*([A-Za-z0-9\-_]+)',
            r'transaction\s*number[:\s]*([A-Za-z0-9\-_]+)',
            r'order\s*id[:\s]*([A-Za-z0-9\-_]+)',
            r'order\s*number[:\s]*([A-Za-z0-9\-_]+)'
        ],
        'transaction_amount': [
            r'amount[:\s]*([\d,\.]+\s*[A-Za-z]*)',
            r'total[:\s]*([\d,\.]+\s*[A-Za-z]*)',
            r'price[:\s]*([\d,\.]+\s*[A-Za-z\$￥]*)',
            r'sum[:\s]*([\d,\.]+\s*[A-Za-z\$￥]*)',
            r'\$\s*([\d,\.]+)',
            r'￥\s*([\d,\.]+)'
        ],
        'payment_date': [
            r'payment\s*date[:\s]*([\d\-\/\s]+)',
            r'date[:\s]*([\d\-\/\s]+)',
            r'transaction\s*date[:\s]*([\d\-\/\s]+)',
            r'invoice\s*date[:\s]*([\d\-\/\s]+)',
            r'(\d{4}[\-\/]\d{1,2}[\-\/]\d{1,2})',
            r'(\d{1,2}[\-\/]\d{1,2}[\-\/]\d{4})'
        ],
        'document_timestamp': [
            r'timestamp[:\s]*([\d\-\/\s:]+)',
            r'time[:\s]*([\d\-\/\s:]+)',
            r'datetime[:\s]*([\d\-\/\s:]+)',
            r'(\d{4}[\-\/]\d{1,2}[\-\/]\d{1,2}\s+\d{1,2}:\d{1,2})',
            r'(\d{1,2}[\-\/]\d{1,2}[\-\/]\d{4}\s+\d{1,2}:\d{1,2})'
        ],
        'customer_country': [
            r'country[:\s]*([A-Za-z\s]+)',
            r'nation[:\s]*([A-Za-z\s]+)',
            r'region[:\s]*([^\n\r]+)',
            r'location[:\s]*([^\n\r]+)'
        ]
    }
    
    # Pattern matching for each keyword
    for key, pattern_list in patterns.items():
        for pattern in pattern_list:
            match = re.search(pattern, text_lower, re.IGNORECASE | re.MULTILINE)
            if match:
                value = match.group(1).strip()
                # Clean extracted value
                value = re.sub(r'[:\s]+$', '', value)  # Remove trailing colons and spaces
                value = value.strip()
                if value and len(value) > 0:
                    extracted_info[key] = value
                    break  # Stop after finding first match
    
    return extracted_info

def save_to_database(filename: str, file_path: str, ocr_text: str, model_used: str, extracted_info: Dict[str, Optional[str]]) -> int:
    """Save extracted information to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Calculate extraction confidence (based on number of successfully extracted fields)
    total_fields = len(extracted_info)
    extracted_fields = sum(1 for v in extracted_info.values() if v is not None)
    confidence = extracted_fields / total_fields if total_fields > 0 else 0.0
    
    cursor.execute('''
        INSERT INTO ocr_records (
            filename, file_path, customer_name, customer_id, transaction_id,
            transaction_amount, payment_date, document_timestamp, customer_country,
            raw_ocr_text, model_used, extraction_confidence
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        filename,
        file_path,
        extracted_info.get('customer_name'),
        extracted_info.get('customer_id'),
        extracted_info.get('transaction_id'),
        extracted_info.get('transaction_amount'),
        extracted_info.get('payment_date'),
        extracted_info.get('document_timestamp'),
        extracted_info.get('customer_country'),
        ocr_text,
        model_used,
        confidence
    ))
    
    record_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return record_id

def get_all_records() -> List[Dict]:
    """Get all database records"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, filename, file_path, processing_time, customer_name, customer_id,
               transaction_id, transaction_amount, payment_date, document_timestamp,
               customer_country, model_used, extraction_confidence
        FROM ocr_records
        ORDER BY processing_time DESC
    ''')
    
    columns = [description[0] for description in cursor.description]
    records = []
    
    for row in cursor.fetchall():
        record = dict(zip(columns, row))
        records.append(record)
    
    conn.close()
    return records

def search_records(customer_name: str = None, customer_id: str = None, transaction_id: str = None, customer_country: str = None) -> List[Dict]:
    """Search database records"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = '''
        SELECT id, filename, file_path, processing_time, customer_name, customer_id,
               transaction_id, transaction_amount, payment_date, document_timestamp,
               customer_country, raw_ocr_text, model_used, extraction_confidence
        FROM ocr_records
        WHERE 1=1
    '''
    params = []
    
    if customer_name:
        query += ' AND customer_name LIKE ?'
        params.append(f'%{customer_name}%')
    
    if customer_id:
        query += ' AND customer_id LIKE ?'
        params.append(f'%{customer_id}%')
    
    if transaction_id:
        query += ' AND transaction_id LIKE ?'
        params.append(f'%{transaction_id}%')
    
    if customer_country:
        query += ' AND customer_country LIKE ?'
        params.append(f'%{customer_country}%')
    
    query += ' ORDER BY processing_time DESC'
    
    try:
        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        records = []
        
        for row in cursor.fetchall():
            record = dict(zip(columns, row))
            # Add ocr_text field for frontend compatibility
            record['ocr_text'] = record.get('raw_ocr_text', '')
            records.append(record)
        
        conn.close()
        return records
        
    except Exception as e:
        conn.close()
        print(f"Search error: {e}")
        return []

def delete_record(record_id: int) -> bool:
    """Delete specified record"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM ocr_records WHERE id = ?', (record_id,))
    affected_rows = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    return affected_rows > 0

def get_database_stats() -> Dict:
    """Get database statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Total records count
    cursor.execute('SELECT COUNT(*) FROM ocr_records')
    total_records = cursor.fetchone()[0]
    
    # Records with successfully extracted information (at least one field is not null)
    cursor.execute('''
        SELECT COUNT(*) FROM ocr_records 
        WHERE customer_name IS NOT NULL 
           OR transaction_amount IS NOT NULL 
           OR transaction_id IS NOT NULL
           OR customer_id IS NOT NULL
    ''')
    extracted_records = cursor.fetchone()[0]
    
    # Records processed today
    cursor.execute('''
        SELECT COUNT(*) FROM ocr_records 
        WHERE DATE(processing_time) = DATE('now')
    ''')
    today_records = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total': total_records,
        'extracted': extracted_records,
        'today': today_records
    }

def advanced_search_records(
    keyword: str = None,
    customer_name: str = None,
    min_amount: float = None,
    max_amount: float = None,
    start_date: str = None,
    end_date: str = None
) -> List[Dict]:
    """Advanced search of database records"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = '''
        SELECT id, filename, file_path, processing_time, customer_name, customer_id,
               transaction_id, transaction_amount, payment_date, document_timestamp,
               customer_country, raw_ocr_text, model_used, extraction_confidence
        FROM ocr_records
        WHERE 1=1
    '''
    params = []
    
    # Keyword search
    if keyword:
        query += ' AND (raw_ocr_text LIKE ? OR filename LIKE ? OR customer_name LIKE ? OR transaction_id LIKE ?)'
        keyword_param = f'%{keyword}%'
        params.extend([keyword_param, keyword_param, keyword_param, keyword_param])
    
    # Customer name search
    if customer_name:
        query += ' AND customer_name LIKE ?'
        params.append(f'%{customer_name}%')
    
    # Amount range search
    if min_amount is not None or max_amount is not None:
        # Extract numeric amount for comparison
        if min_amount is not None:
            query += ' AND CAST(REPLACE(REPLACE(REPLACE(transaction_amount, ",", ""), "$", ""), "￥", "") AS REAL) >= ?'
            params.append(min_amount)
        if max_amount is not None:
            query += ' AND CAST(REPLACE(REPLACE(REPLACE(transaction_amount, ",", ""), "$", ""), "￥", "") AS REAL) <= ?'
            params.append(max_amount)
    
    # Date range search
    if start_date:
        query += ' AND DATE(processing_time) >= DATE(?)'
        params.append(start_date)
    if end_date:
        query += ' AND DATE(processing_time) <= DATE(?)'
        params.append(end_date)
    
    query += ' ORDER BY processing_time DESC'
    
    try:
        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        records = []
        
        for row in cursor.fetchall():
            record = dict(zip(columns, row))
            records.append(record)
        
        conn.close()
        return records
        
    except Exception as e:
        conn.close()
        print(f"Advanced search error: {e}")
        return []

# Initialize database
if __name__ == '__main__':
    init_database()