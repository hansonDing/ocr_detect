# SQLite Database Query Guide

## 📊 Database Overview

**Database File Location**: `ocr_data.db`  
**Main Table**: `ocr_records`

### Table Structure
```sql
CREATE TABLE ocr_records (
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
);
```

## 🔧 Query Methods

### Method 1: Query Using Python Code

#### 1.1 Import Existing Functions
```python
from database import get_all_records, search_records, delete_record

# Get all records
all_records = get_all_records()
print(f"Total {len(all_records)} records")

# Search records
search_results = search_records(keyword="customer")
print(f"Found {len(search_results)} related records")

# Search by customer name
customer_records = search_records(customer_name="John Doe")

# Search by transaction ID
transaction_records = search_records(transaction_id="TXN123")
```

#### 1.2 Custom SQL Queries
```python
import sqlite3
import os

# Connect to database
db_path = os.path.join(os.path.dirname(__file__), 'ocr_data.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Query examples
# 1. View all records
cursor.execute("SELECT * FROM ocr_records ORDER BY processing_time DESC")
records = cursor.fetchall()

# 2. Count records
cursor.execute("SELECT COUNT(*) FROM ocr_records")
count = cursor.fetchone()[0]
print(f"Total {count} records in database")

# 3. Query by date range
cursor.execute("""
    SELECT * FROM ocr_records 
    WHERE processing_time >= '2024-01-01' 
    AND processing_time <= '2024-12-31'
    ORDER BY processing_time DESC
""")
date_records = cursor.fetchall()

# 4. Query all records for specific customer
cursor.execute("""
    SELECT * FROM ocr_records 
    WHERE customer_name LIKE '%John%' 
    ORDER BY processing_time DESC
""")
customer_records = cursor.fetchall()

# 5. Statistics of model usage
cursor.execute("""
    SELECT model_used, COUNT(*) as count 
    FROM ocr_records 
    GROUP BY model_used
""")
model_stats = cursor.fetchall()

# 6. Query high confidence extraction records
cursor.execute("""
    SELECT * FROM ocr_records 
    WHERE extraction_confidence > 0.5 
    ORDER BY extraction_confidence DESC
""")
high_confidence_records = cursor.fetchall()

# Close connection
conn.close()
```

### Method 2: Using SQLite Command Line Tool

#### 2.1 Open Database
```bash
# Execute in project directory
sqlite3 ocr_data.db
```

#### 2.2 Common Query Commands
```sql
-- View table structure
.schema ocr_records

-- View all tables
.tables

-- Set display mode
.mode column
.headers on

-- Basic query
SELECT * FROM ocr_records LIMIT 10;

-- Count records
SELECT COUNT(*) as total_records FROM ocr_records;

-- View latest records sorted by date
SELECT id, filename, customer_name, processing_time 
FROM ocr_records 
ORDER BY processing_time DESC 
LIMIT 5;

-- Query records containing specific keywords
SELECT id, filename, customer_name, transaction_amount 
FROM ocr_records 
WHERE raw_ocr_text LIKE '%invoice%' OR raw_ocr_text LIKE '%receipt%';

-- Count customers by country
SELECT customer_country, COUNT(*) as count 
FROM ocr_records 
WHERE customer_country IS NOT NULL 
GROUP BY customer_country 
ORDER BY count DESC;

-- Query transactions in specific amount range
SELECT * FROM ocr_records 
WHERE transaction_amount LIKE '%100%' OR transaction_amount LIKE '%1000%';

-- Exit SQLite
.quit
```

### Method 3: Using Web Interface Query

Visit `http://127.0.0.1:5000` and use the "Database Record Management" feature:

1. **View All Records**: Click the "Show All" button
2. **Search Records**: Enter keywords in the search box and click the "Search" button
3. **Delete Records**: Click the "🗑️ Delete" button next to the record

### Method 4: Using API Interface Query

#### 4.1 Get All Records
```bash
curl http://127.0.0.1:5000/database/records
```

#### 4.2 Search Records
```bash
# Search by keyword
curl "http://127.0.0.1:5000/database/search?keyword=customer"

# Search by customer name
curl "http://127.0.0.1:5000/database/search?customer_name=John Doe"

# Search by transaction ID
curl "http://127.0.0.1:5000/database/search?transaction_id=TXN123"
```

#### 4.3 Delete Records
```bash
curl -X DELETE http://127.0.0.1:5000/database/record/1
```

## 📈 Advanced Query Examples

### Data Analysis Queries
```python
import sqlite3
import pandas as pd

# Use pandas for data analysis
conn = sqlite3.connect('ocr_data.db')

# Read data into DataFrame
df = pd.read_sql_query("SELECT * FROM ocr_records", conn)

# Statistical analysis
print("=== Data Statistics ===")
print(f"Total records: {len(df)}")
print(f"Unique customers: {df['customer_name'].nunique()}")
print(f"Average extraction confidence: {df['extraction_confidence'].mean():.2f}")

# Statistics by model
model_stats = df['model_used'].value_counts()
print("\n=== Model Usage Statistics ===")
print(model_stats)

# Statistics by date
df['processing_date'] = pd.to_datetime(df['processing_time']).dt.date
daily_stats = df.groupby('processing_date').size()
print("\n=== Daily Processing Volume ===")
print(daily_stats.tail())

conn.close()
```

### Complex Conditional Queries
```sql
-- Query records from last 7 days with extraction confidence > 0.3
SELECT id, filename, customer_name, extraction_confidence, processing_time
FROM ocr_records 
WHERE processing_time >= datetime('now', '-7 days') 
AND extraction_confidence > 0.3
ORDER BY extraction_confidence DESC;

-- Query records with amount information and non-empty customer country
SELECT id, filename, customer_name, transaction_amount, customer_country
FROM ocr_records 
WHERE transaction_amount IS NOT NULL 
AND customer_country IS NOT NULL
AND transaction_amount != ''
AND customer_country != '';

-- Calculate average extraction confidence for each model
SELECT model_used, 
       COUNT(*) as record_count,
       AVG(extraction_confidence) as avg_confidence,
       MAX(extraction_confidence) as max_confidence
FROM ocr_records 
GROUP BY model_used
ORDER BY avg_confidence DESC;
```

## 🛠️ Database Maintenance

### Backup Database
```bash
# Create backup
cp ocr_data.db ocr_data_backup_$(date +%Y%m%d).db

# Or use SQLite command
sqlite3 ocr_data.db ".backup ocr_data_backup.db"
```

### Clean Data
```sql
-- Delete records older than 7 days
DELETE FROM ocr_records 
WHERE processing_time < datetime('now', '-7 days');

-- Delete records with extraction confidence of 0
DELETE FROM ocr_records 
WHERE extraction_confidence = 0.0;

-- Compress database
VACUUM;
```

### Index Optimization
```sql
-- Create indexes for commonly queried fields
CREATE INDEX IF NOT EXISTS idx_processing_time ON ocr_records(processing_time);
CREATE INDEX IF NOT EXISTS idx_customer_name ON ocr_records(customer_name);
CREATE INDEX IF NOT EXISTS idx_transaction_id ON ocr_records(transaction_id);
CREATE INDEX IF NOT EXISTS idx_confidence ON ocr_records(extraction_confidence);
```

## 💡 Usage Recommendations

1. **Regular Backup**: Recommend daily backup of database files
2. **Index Optimization**: Create indexes for frequently queried fields
3. **Data Cleanup**: Regularly clean up useless or expired records
4. **Monitor Size**: Pay attention to database file size to avoid performance impact
5. **Secure Access**: Restrict database file access permissions in production environment

## 🔍 Troubleshooting

### Common Issues
1. **Database Locked**: Ensure no other programs are accessing the database
2. **Permission Issues**: Check read/write permissions for database file
3. **Encoding Issues**: Ensure Chinese characters display correctly
4. **Connection Timeout**: Pay attention to connection timeout settings for long queries

### Repair Commands
```sql
-- Check database integrity
PRAGMA integrity_check;

-- Repair database
PRAGMA quick_check;
```