"""Test accessing actual SEC filing content"""
import os
import requests
from bs4 import BeautifulSoup
import re
from dotenv import load_dotenv

load_dotenv()

def test_filing_access(filing_url, filing_type):
    """Test accessing and parsing a SEC filing document"""
    print(f"\n🔍 Testing access to {filing_type}: {filing_url}")
    
    try:
        # Use proper headers to avoid being blocked
        headers = {
            'User-Agent': 'SEC Filing Parser 1.0 (contact@example.com)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
        }
        
        response = requests.get(filing_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            print(f"✅ Successfully accessed {filing_type}")
            
            # Parse the content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Get some basic statistics
            text_content = soup.get_text()
            print(f"📊 Content length: {len(text_content):,} characters")
            
            # Look for financial statement indicators
            financial_indicators = [
                'CONSOLIDATED STATEMENTS OF OPERATIONS',
                'CONSOLIDATED BALANCE SHEETS', 
                'CONSOLIDATED STATEMENTS OF CASH FLOWS',
                'Net sales',
                'Total revenue',
                'Net income',
                'Total assets'
            ]
            
            found_indicators = []
            for indicator in financial_indicators:
                if indicator.lower() in text_content.lower():
                    found_indicators.append(indicator)
            
            if found_indicators:
                print(f"💰 Found financial indicators: {', '.join(found_indicators[:3])}...")
                
                # Try to extract some sample numbers
                # Look for dollar amounts in millions/billions
                dollar_pattern = r'\$[\d,]+(?:\.\d+)?\s*(?:million|billion|thousand)?'
                dollar_matches = re.findall(dollar_pattern, text_content, re.IGNORECASE)
                
                if dollar_matches:
                    print(f"💵 Sample dollar amounts found: {dollar_matches[:5]}...")
                else:
                    print("❌ No dollar amounts detected")
            else:
                print("❌ No financial statement indicators found")
                
            return True
            
        elif response.status_code == 403:
            print(f"❌ Access denied (403) - SEC blocking automated access")
            return False
        else:
            print(f"❌ HTTP {response.status_code} error")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Network error: {e}")
        return False
    except Exception as e:
        print(f"❌ Parsing error: {e}")
        return False

print("Testing SEC Filing Content Access...")
print("=" * 60)

# Test URLs from our previous SEC API call
test_urls = [
    ("https://www.sec.gov/Archives/edgar/data/1018724/000101872425000036/amzn-20250331.htm", "10-Q Q1 2025"),
    ("https://www.sec.gov/Archives/edgar/data/1018724/000101872425000004/amzn-20241231.htm", "10-K 2024")
]

results = []
for url, filing_type in test_urls:
    success = test_filing_access(url, filing_type)
    results.append((filing_type, success))

print("\n" + "=" * 60)
print("SUMMARY:")
for filing_type, success in results:
    status = "✅ SUCCESS" if success else "❌ BLOCKED"
    print(f"{filing_type}: {status}")

print("\nConclusions:")
print("1. SEC filing URLs are publicly accessible")
print("2. Content can be parsed if access is granted")
print("3. May need proper SEC compliance headers")
print("4. Financial data extraction is technically possible")
print("5. Need to handle rate limiting and access restrictions")
