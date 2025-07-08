# SQLite Database Query Command Reference

## Database Information
- **Database File**: `ocr_data.db`
- **Main Table**: `ocr_records`
- **Location**: Project root directory

## Table Structure
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

## Query Methods

### 1. Python Script Query

#### Basic Connection
```python
import sqlite3

# Connect to database
conn = sqlite3.connect('ocr_data.db')
conn.row_factory = sqlite3.Row  # Support column name access
cursor = conn.cursor()

# Execute query
cursor.execute("SELECT * FROM ocr_records")
results = cursor.fetchall()

# Close connection
conn.close()
```

#### Common Query Examples
```python
# 1. View all records
cursor.execute("SELECT * FROM ocr_records ORDER BY processing_time DESC")

# 2. Query by ID
cursor.execute("SELECT * FROM ocr_records WHERE id = ?", (record_id,))

# 3. Query by filename
cursor.execute("SELECT * FROM ocr_records WHERE filename LIKE ?", (f'%{filename}%',))

# 4. Query by customer name
cursor.execute("SELECT * FROM ocr_records WHERE customer_name LIKE ?", (f'%{name}%',))

# 5. Keyword search
cursor.execute("""
    SELECT * FROM ocr_records 
    WHERE raw_ocr_text LIKE ? OR filename LIKE ?
""", (f'%{keyword}%', f'%{keyword}%'))

# 6. Count records
cursor.execute("SELECT COUNT(*) FROM ocr_records")

# 7. Query by date range
cursor.execute("""
    SELECT * FROM ocr_records 
    WHERE processing_time BETWEEN ? AND ?
""", (start_date, end_date))
```

### 2. Using Provided Query Scripts

#### Interactive Query Tool
```bash
python query_database.py
```
Features include:
- View database information
- View recent records
- Query by customer
- Keyword search
- Export to CSV
- Custom SQL queries

#### Simple Query Example
```bash
python simple_query_example.py
```
Demonstrates basic query operations:
- Display table structure
- Count records
- Display all records
- Search functionality
- Get specific records

### 3. Web Interface Query

After starting the Flask application, you can query through the following API endpoints:

```bash
# Start application
python app.py
```

#### API Endpoints
- `GET /database/records` - Get all records
- `GET /database/search?q=keyword` - Search records
- `DELETE /database/record/<id>` - Delete record

#### Browser Access
- Open `http://localhost:5000`
- Use "Database Record Management" feature

## Advanced Query Examples

### Data Analysis Queries
```python
# Statistics by OCR model
cursor.execute("""
    SELECT model_used, COUNT(*) as count 
    FROM ocr_records 
    GROUP BY model_used
""")

# Statistics by date
cursor.execute("""
    SELECT DATE(processing_time) as date, COUNT(*) as count 
    FROM ocr_records 
    GROUP BY DATE(processing_time)
    ORDER BY date DESC
""")

# Extraction success rate statistics
cursor.execute("""
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN customer_name IS NOT NULL THEN 1 ELSE 0 END) as extracted
    FROM ocr_records
""")
```

### Complex Conditional Queries
```python
# Multi-condition query
cursor.execute("""
    SELECT * FROM ocr_records 
    WHERE model_used = 'OCR API' 
    AND extraction_confidence > 0.8
    AND processing_time >= date('now', '-7 days')
    ORDER BY extraction_confidence DESC
""")

# Subquery example
cursor.execute("""
    SELECT * FROM ocr_records 
    WHERE processing_time = (
        SELECT MAX(processing_time) FROM ocr_records
    )
""")
```

## Data Export

### Export to CSV
```python
import csv

cursor.execute("SELECT * FROM ocr_records")
records = cursor.fetchall()

with open('ocr_records.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    # Write header
    writer.writerow([description[0] for description in cursor.description])
    # Write data
    writer.writerows(records)
```

### Export to JSON
```python
import json

cursor.execute("SELECT * FROM ocr_records")
records = [dict(row) for row in cursor.fetchall()]

with open('ocr_records.json', 'w', encoding='utf-8') as f:
    json.dump(records, f, ensure_ascii=False, indent=2, default=str)
```

## Database Maintenance

### Backup Database
```bash
# Copy database file
copy ocr_data.db ocr_data_backup.db
```

### Clean Old Data
```python
# Delete records older than 30 days
cursor.execute("""
    DELETE FROM ocr_records 
    WHERE processing_time < date('now', '-30 days')
""")
conn.commit()
```

### Optimize Database
```python
# Rebuild indexes and optimize
cursor.execute("VACUUM")
cursor.execute("ANALYZE")
```

## Notes

1. **Security**: Use parameterized queries to avoid SQL injection
2. **Performance**: Create indexes for frequently queried fields
3. **Backup**: Regularly backup database files
4. **Connection Management**: Close database connections promptly
5. **Error Handling**: Use try-except to handle database exceptions

## Quick Start

1. Ensure database file exists: `ocr_data.db`
2. Run query example: `python simple_query_example.py`
3. Use interactive tool: `python query_database.py`
4. Through web interface: Start `python app.py` then access browser

Now you can query and manage the OCR database through multiple methods!