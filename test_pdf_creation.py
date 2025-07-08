#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create a test PDF file for testing PDF OCR functionality
"""

import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def create_test_pdf():
    """Create a test PDF file with sample text"""
    try:
        # Create PDF file
        pdf_path = "test_document.pdf"
        c = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter
        
        # Page 1
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, height - 100, "Test Document for OCR Processing")
        
        c.setFont("Helvetica", 12)
        c.drawString(100, height - 150, "Customer Name: John Smith")
        c.drawString(100, height - 170, "Customer ID: CS123456")
        c.drawString(100, height - 190, "Transaction ID: TXN789012")
        c.drawString(100, height - 210, "Transaction Amount: $1,250.00")
        c.drawString(100, height - 230, "Transaction Date: 2024-01-15")
        c.drawString(100, height - 250, "Account Number: 4567-8901-2345")
        c.drawString(100, height - 270, "Bank Name: Test Bank")
        
        c.drawString(100, height - 320, "This is a test document created to verify")
        c.drawString(100, height - 340, "the PDF processing functionality of the OCR system.")
        c.drawString(100, height - 360, "It contains sample transaction information")
        c.drawString(100, height - 380, "that should be extracted by the OCR engine.")
        
        # Add a simple table
        c.drawString(100, height - 430, "Transaction History:")
        c.drawString(100, height - 450, "Date        Amount      Description")
        c.drawString(100, height - 470, "2024-01-15  $1,250.00   Payment Received")
        c.drawString(100, height - 490, "2024-01-10  $500.00     Deposit")
        c.drawString(100, height - 510, "2024-01-05  $75.00      Service Fee")
        
        # Start new page
        c.showPage()
        
        # Page 2
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, height - 100, "Page 2 - Additional Information")
        
        c.setFont("Helvetica", 12)
        c.drawString(100, height - 150, "Customer Address:")
        c.drawString(120, height - 170, "123 Main Street")
        c.drawString(120, height - 190, "Anytown, ST 12345")
        c.drawString(120, height - 210, "United States")
        
        c.drawString(100, height - 260, "Contact Information:")
        c.drawString(120, height - 280, "Phone: (555) 123-4567")
        c.drawString(120, height - 300, "Email: john.smith@email.com")
        
        c.drawString(100, height - 350, "This is the second page of the test document.")
        c.drawString(100, height - 370, "It demonstrates multi-page PDF processing")
        c.drawString(100, height - 390, "capabilities of the OCR system.")
        
        # Save the PDF
        c.save()
        
        print(f"Test PDF created successfully: {pdf_path}")
        print(f"File size: {os.path.getsize(pdf_path)} bytes")
        return pdf_path
        
    except Exception as e:
        print(f"Error creating test PDF: {e}")
        return None

if __name__ == "__main__":
    create_test_pdf()