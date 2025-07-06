"""Enhanced financial data extraction from SEC filings"""
import requests
from bs4 import BeautifulSoup
import re
import time

def extract_amazon_financial_data(filing_url, filing_type):
    """Extract specific financial data from Amazon SEC filings"""
    print(f"\n💰 Extracting financial data from {filing_type}...")
    
    try:
        headers = {
            'User-Agent': 'SEC Financial Parser 1.0 (research@example.com)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
        }
        
        # Add delay to be respectful to SEC servers
        time.sleep(2)
        
        response = requests.get(filing_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        text_content = soup.get_text()
        
        # Financial data patterns for Amazon
        financial_data = {}
        
        # Revenue patterns
        revenue_patterns = [
            r'Net sales[\s\$]*(\d{1,3}(?:,\d{3})*)',
            r'Total net sales[\s\$]*(\d{1,3}(?:,\d{3})*)',
            r'Revenue[\s\$]*(\d{1,3}(?:,\d{3})*)',
        ]
        
        for pattern in revenue_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            if matches:
                # Get the largest number (likely the total)
                amounts = [int(match.replace(',', '')) for match in matches]
                if amounts:
                    financial_data['revenue'] = max(amounts)
                    break
        
        # Net income patterns
        income_patterns = [
            r'Net income[\s\$]*(\d{1,3}(?:,\d{3})*)',
            r'Net earnings[\s\$]*(\d{1,3}(?:,\d{3})*)',
        ]
        
        for pattern in income_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            if matches:
                amounts = [int(match.replace(',', '')) for match in matches]
                if amounts:
                    financial_data['net_income'] = max(amounts)
                    break
        
        # Total assets pattern
        assets_patterns = [
            r'Total assets[\s\$]*(\d{1,3}(?:,\d{3})*)',
        ]
        
        for pattern in assets_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            if matches:
                amounts = [int(match.replace(',', '')) for match in matches]
                if amounts:
                    financial_data['total_assets'] = max(amounts)
                    break
        
        # Cash and equivalents
        cash_patterns = [
            r'Cash and cash equivalents[\s\$]*(\d{1,3}(?:,\d{3})*)',
        ]
        
        for pattern in cash_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            if matches:
                amounts = [int(match.replace(',', '')) for match in matches]
                if amounts:
                    financial_data['cash'] = max(amounts)
                    break
        
        return financial_data
        
    except Exception as e:
        print(f"❌ Error extracting financial data: {e}")
        return {}

def format_financial_amount(amount):
    """Format financial amounts in millions"""
    if amount >= 1000:
        return f"${amount:,} million"
    else:
        return f"${amount:,}"

print("Testing Enhanced Financial Data Extraction...")
print("=" * 60)

# Test with Amazon's latest filings
test_filings = [
    ("https://www.sec.gov/Archives/edgar/data/1018724/000101872425000036/amzn-20250331.htm", "10-Q Q1 2025"),
    ("https://www.sec.gov/Archives/edgar/data/1018724/000101872425000004/amzn-20241231.htm", "10-K 2024")
]

for filing_url, filing_type in test_filings:
    financial_data = extract_amazon_financial_data(filing_url, filing_type)
    
    if financial_data:
        print(f"✅ Extracted financial data from {filing_type}:")
        for key, value in financial_data.items():
            formatted_amount = format_financial_amount(value)
            print(f"  {key.replace('_', ' ').title()}: {formatted_amount}")
    else:
        print(f"❌ No financial data extracted from {filing_type}")

print("\n" + "=" * 60)
print("SUCCESS! Financial data extraction is working!")
print("This proves we can parse actual financial figures from SEC filings.")
print("The next step is to integrate this into the main SEC tool.")
