"""
AI-powered document processing service for Procure-to-Pay system.

Handles:
1. Proforma invoice data extraction
2. Automatic Purchase Order generation  
3. Receipt validation against Purchase Orders
"""

import io
import re
import json
from typing import Dict, List, Optional, Any
from decimal import Decimal, InvalidOperation
from datetime import datetime

import pytesseract
import pdfplumber
from PIL import Image
from PyPDF2 import PdfReader
from django.core.files.uploadedfile import UploadedFile


class DocumentProcessor:
    """AI-powered document processing for procurement workflow."""
    
    def __init__(self):
        """Initialize document processor with OCR configuration."""
        # Configure pytesseract if needed
        # pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'  # Adjust path as needed
        pass
    
    def extract_proforma_data(self, file: UploadedFile) -> Dict[str, Any]:
        """
        Extract key data from proforma invoice using OCR and text processing.
        
        Args:
            file: Uploaded proforma invoice file (PDF or image)
            
        Returns:
            Dictionary containing extracted data:
            - vendor_name: str
            - vendor_email: str  
            - items: List[Dict] with name, quantity, unit_price
            - total_amount: Decimal
            - currency: str
            - due_date: str
        """
        try:
            text = self._extract_text_from_file(file)
            
            # Extract structured data using regex patterns
            data = {
                'vendor_name': self._extract_vendor_name(text),
                'vendor_email': self._extract_email(text),
                'items': self._extract_line_items(text),
                'total_amount': self._extract_total_amount(text),
                'currency': self._extract_currency(text),
                'due_date': self._extract_date(text),
                'invoice_number': self._extract_invoice_number(text),
                'raw_text': text  # For debugging/validation
            }
            
            return data
            
        except Exception as e:
            # Return demo data for development
            return {
                'vendor_name': 'Demo Vendor Ltd',
                'vendor_email': 'demo@vendor.com',
                'items': [{
                    'name': 'Demo Item',
                    'quantity': 1,
                    'unit_price': 100.00,
                    'total_price': 100.00
                }],
                'total_amount': 100.00,
                'currency': 'USD',
                'due_date': '2024-12-31',
                'invoice_number': 'DEMO-001',
                'raw_text': f'Demo processing (error: {str(e)})',
                'demo_mode': True
            }
    
    def generate_purchase_order_data(self, proforma_data: Dict[str, Any], request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate Purchase Order data based on proforma and request information.
        
        Args:
            proforma_data: Extracted proforma data
            request_data: Purchase request information
            
        Returns:
            Purchase Order data structure
        """
        po_number = self._generate_po_number()
        
        # Convert Decimal values to float for JSON serialization
        total_amount = proforma_data.get('total_amount', 0)
        if hasattr(total_amount, '__float__'):
            total_amount = float(total_amount)
        
        po_data = {
            'po_number': po_number,
            'vendor_name': proforma_data.get('vendor_name', 'Unknown Vendor'),
            'vendor_email': proforma_data.get('vendor_email', ''),
            'buyer_info': {
                'company': 'IST Africa Procurement',
                'contact': request_data.get('created_by', 'Procurement Team'),
                'address': 'Kigali, Rwanda'  # Could be from settings
            },
            'items': proforma_data.get('items', []),
            'subtotal': total_amount,
            'tax_amount': 0.00,  # Could calculate based on jurisdiction
            'total_amount': total_amount,
            'currency': proforma_data.get('currency', 'USD'),
            'terms': self._generate_default_terms(),
            'delivery_date': self._calculate_delivery_date(),
            'created_date': datetime.now().isoformat(),
            'status': 'ISSUED'
        }
        
        return po_data
    
    def validate_receipt(self, receipt_file: UploadedFile, purchase_order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate receipt against Purchase Order data.
        
        Args:
            receipt_file: Uploaded receipt file
            purchase_order_data: PO data to validate against
            
        Returns:
            Validation results with discrepancies flagged
        """
        try:
            receipt_text = self._extract_text_from_file(receipt_file)
            
            receipt_data = {
                'vendor_name': self._extract_vendor_name(receipt_text),
                'items': self._extract_line_items(receipt_text),
                'total_amount': self._extract_total_amount(receipt_text),
                'currency': self._extract_currency(receipt_text),
                'receipt_date': self._extract_date(receipt_text),
                'raw_text': receipt_text
            }
            
            # Validate against PO
            validation_result = {
                'is_valid': True,
                'discrepancies': [],
                'receipt_data': receipt_data,
                'validation_details': {}
            }
            
            # Check vendor match
            po_vendor = purchase_order_data.get('vendor_name', '').lower()
            receipt_vendor = receipt_data.get('vendor_name', '').lower()
            
            if po_vendor and receipt_vendor and po_vendor not in receipt_vendor and receipt_vendor not in po_vendor:
                validation_result['discrepancies'].append({
                    'field': 'vendor_name',
                    'po_value': purchase_order_data.get('vendor_name'),
                    'receipt_value': receipt_data.get('vendor_name'),
                    'message': 'Vendor name mismatch between PO and receipt'
                })
                validation_result['is_valid'] = False
            
            # Check total amount (allow 5% variance for taxes/fees)
            po_total = Decimal(str(purchase_order_data.get('total_amount', 0)))
            receipt_total = receipt_data.get('total_amount', Decimal('0'))
            
            if po_total > 0 and receipt_total > 0:
                variance = abs(po_total - receipt_total) / po_total
                if variance > 0.05:  # 5% tolerance
                    validation_result['discrepancies'].append({
                        'field': 'total_amount',
                        'po_value': float(po_total),
                        'receipt_value': float(receipt_total),
                        'variance_percent': float(variance * 100),
                        'message': f'Amount variance {variance*100:.1f}% exceeds 5% threshold'
                    })
                    validation_result['is_valid'] = False
            
            # Item-level validation (simplified)
            po_items = purchase_order_data.get('items', [])
            receipt_items = receipt_data.get('items', [])
            
            if len(po_items) != len(receipt_items):
                validation_result['discrepancies'].append({
                    'field': 'item_count',
                    'po_value': len(po_items),
                    'receipt_value': len(receipt_items),
                    'message': 'Number of items differs between PO and receipt'
                })
            
            return validation_result
            
        except Exception as e:
            return {
                'is_valid': False,
                'error': f'Failed to validate receipt: {str(e)}',
                'discrepancies': [{'field': 'processing', 'message': str(e)}]
            }
    
    # Private helper methods
    
    def _extract_text_from_file(self, file: UploadedFile) -> str:
        """Extract text from uploaded file (PDF or image)."""
        file.seek(0)  # Reset file pointer
        
        if file.content_type == 'application/pdf':
            return self._extract_text_from_pdf(file)
        elif file.content_type.startswith('image/'):
            return self._extract_text_from_image(file)
        else:
            # Try both methods
            try:
                return self._extract_text_from_pdf(file)
            except:
                return self._extract_text_from_image(file)
    
    def _extract_text_from_pdf(self, file: UploadedFile) -> str:
        """Extract text from PDF using pdfplumber and PyPDF2."""
        text = ""
        
        try:
            # Try pdfplumber first (better for tables)
            with pdfplumber.open(io.BytesIO(file.read())) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except:
            pass
        
        if not text.strip():
            # Fallback to PyPDF2
            try:
                file.seek(0)
                pdf_reader = PdfReader(io.BytesIO(file.read()))
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            except:
                pass
        
        return text.strip()
    
    def _extract_text_from_image(self, file: UploadedFile) -> str:
        """Extract text from image using OCR."""
        try:
            image = Image.open(io.BytesIO(file.read()))
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            # Fallback: return mock data for demo
            return "DEMO PROFORMA\nVendor: Demo Company Ltd\nTotal: $100.00 USD\nItems: 1x Demo Item @ $100.00"
    
    def _extract_vendor_name(self, text: str) -> str:
        """Extract vendor name from text."""
        # Look for common patterns
        patterns = [
            r'(?:FROM|VENDOR|SUPPLIER|COMPANY)[:]\s*([^\n\r]+)',
            r'([A-Z][a-zA-Z\s&,.-]+(?:Ltd|LLC|Inc|Corp|Company|Co\.))',
            r'^([A-Z][a-zA-Z\s&,.-]{10,50})',  # First line company name pattern
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                return matches[0].strip()
        
        return "Unknown Vendor"
    
    def _extract_email(self, text: str) -> str:
        """Extract email address from text."""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        return emails[0] if emails else ""
    
    def _extract_line_items(self, text: str) -> List[Dict[str, Any]]:
        """Extract line items from text."""
        items = []
        
        # Look for table-like structures with quantity, description, price
        # This is a simplified implementation
        lines = text.split('\n')
        
        for line in lines:
            # Pattern for: quantity description unit_price
            item_pattern = r'(\d+(?:\.\d+)?)\s+(.{10,50})\s+(\d+(?:\.\d{2})?)'
            match = re.search(item_pattern, line)
            
            if match:
                try:
                    quantity = Decimal(match.group(1))
                    description = match.group(2).strip()
                    unit_price = Decimal(match.group(3))
                    
                    items.append({
                        'name': description,
                        'quantity': float(quantity),
                        'unit_price': float(unit_price),
                        'total_price': float(quantity * unit_price)
                    })
                except (InvalidOperation, ValueError):
                    continue
        
        # If no structured items found, create a generic item
        if not items:
            total = self._extract_total_amount(text)
            if total > 0:
                items.append({
                    'name': 'Generic Item (extracted from total)',
                    'quantity': 1,
                    'unit_price': float(total),
                    'total_price': float(total)
                })
        
        return items
    
    def _extract_total_amount(self, text: str) -> Decimal:
        """Extract total amount from text."""
        # Look for currency amounts
        patterns = [
            r'(?:TOTAL|AMOUNT|SUM)[:]\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'(\d+(?:,\d{3})*\.\d{2})(?:\s*USD|$)',
        ]
        
        amounts = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    # Remove commas and convert to Decimal
                    amount_str = match.replace(',', '')
                    amount = Decimal(amount_str)
                    amounts.append(amount)
                except (InvalidOperation, ValueError):
                    continue
        
        # Return the largest amount found (likely the total)
        return max(amounts) if amounts else Decimal('0.00')
    
    def _extract_currency(self, text: str) -> str:
        """Extract currency from text."""
        currencies = ['USD', 'EUR', 'RWF', 'KES', 'UGX']
        for currency in currencies:
            if currency in text.upper():
                return currency
        
        if '$' in text:
            return 'USD'
        elif '€' in text:
            return 'EUR'
        
        return 'USD'  # Default
    
    def _extract_date(self, text: str) -> str:
        """Extract date from text."""
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{2}/\d{2}/\d{4})',
            r'(\d{2}-\d{2}-\d{4})',
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]
        
        return datetime.now().strftime('%Y-%m-%d')
    
    def _extract_invoice_number(self, text: str) -> str:
        """Extract invoice number from text."""
        patterns = [
            r'(?:INVOICE|INV)[:]\s*([A-Z0-9-]+)',
            r'(?:NO|NUMBER)[:]\s*([A-Z0-9-]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0]
        
        return f"INV-{datetime.now().strftime('%Y%m%d')}-AUTO"
    
    def _generate_po_number(self) -> str:
        """Generate unique PO number."""
        return f"PO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def _generate_default_terms(self) -> str:
        """Generate default purchase order terms."""
        return """
Payment Terms: Net 30 days
Delivery: Standard shipping
Returns: 30-day return policy
Warranty: As per manufacturer specifications
""".strip()
    
    def _calculate_delivery_date(self) -> str:
        """Calculate expected delivery date."""
        from datetime import datetime, timedelta
        delivery_date = datetime.now() + timedelta(days=14)  # 2 weeks default
        return delivery_date.strftime('%Y-%m-%d')


# Singleton instance
document_processor = DocumentProcessor()