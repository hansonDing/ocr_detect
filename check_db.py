#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from database import get_all_records

records = get_all_records()
print(f"Database record count: {len(records)}")

if records:
    print("\nLatest records:")
    for record in records[-3:]:
        print(f"ID: {record.get('id')}")
        print(f"Customer Name: {record.get('customer_name')}")
        print(f"Customer ID: {record.get('customer_id')}")
        print(f"Transaction ID: {record.get('transaction_id')}")
        print(f"Transaction Amount: {record.get('transaction_amount')}")
        print(f"Payment Date: {record.get('payment_date')}")
        print(f"Document Timestamp: {record.get('document_timestamp')}")
        print(f"Customer Country: {record.get('customer_country')}")
        print("-" * 40)
else:
    print("No records in database")