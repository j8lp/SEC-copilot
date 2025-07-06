"""Test parsing financial data from SEC filing documents"""
import os
import requests
from bs4 import BeautifulSoup
import re
from sec_api import QueryApi
from dotenv import load_dotenv

load_dotenv()

def extract_financial_data(filing_url):
    """Extract financial data from SEC filing HTML"""
    print(f"📄 Attempting to parse: {filing_url}")
    
    try:
        # Use proper headers to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        response = requests.get(filing_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for financial data patterns
        text = soup.get_text()
        
        # Common financial statement patterns
        patterns = {
            'revenue': r'(?:Net sales|Total revenue|Revenue).*?(\$[\d,]+(?:\.\d+)?)\s*(?:million|billion|thousand)?',
            'net_income': r'(?:Net income|Net earnings).*?(\$[\d,]+(?:\.\d+)?)\s*(?:million|billion|thousand)?',
            'total_assets': r'(?:Total assets).*?(\$[\d,]+(?:\.\d+)?)\s*(?:million|billion|thousand)?',
            'cash': r'(?:Cash and cash equivalents).*?(\$[\d,]+(?:\.\d+)?)\s*(?:million|billion|thousand)?'
        }
        
        financial_data = {}
        
        for key, pattern in patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                financial_data[key] = matches[:3]  # Take first 3 matches
        
        return financial_data
        
    except requests.RequestException as e:
        print(f"❌ Network error: {e}")
        return None
    except Exception as e:
        print(f"❌ Parsing error: {e}")
        return None

print("Testing financial data extraction...")
print("=" * 50)

try:
    queryApi = QueryApi(api_key=os.getenv('SEC_API_KEY'))
    
    # Get Amazon's latest 10-K
    search_query = {
        "query": 'ticker:AMZN AND formType:"10-K"',
        "from": "0",
        "size": "1",
        "sort": [{"filedAt": {"order": "desc"}}]
    }
    
    response = queryApi.get_filings(search_query)
    
    if response.get("filings"):
        filing = response["filings"][0]
        filing_url = filing.get('linkToFilingDetails')
        
        if filing_url:
            financial_data = extract_financial_data(filing_url)
            
            if financial_data:
                print("💰 Financial data found:")
                for key, values in financial_data.items():
                    print(f"  {key}: {values}")
            else:
                print("❌ No financial data extracted")
        else:
            print("❌ No filing URL found")
    else:
        print("❌ No filings found")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("Test complete!")
