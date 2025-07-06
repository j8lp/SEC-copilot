"""Test SEC API responses and financial parsing"""
import os
from sec_api import QueryApi
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("Testing SEC API and Financial Parsing...")
print("=" * 50)

try:
    # Initialize SEC API
    sec_api_key = os.getenv('SEC_API_KEY')
    queryApi = QueryApi(api_key=sec_api_key)
    
    # Test query for Amazon
    search_query = {
        "query": 'ticker:AMZN AND formType:("10-K" OR "10-Q")',
        "from": "0",
        "size": "2",
        "sort": [{"filedAt": {"order": "desc"}}]
    }
    
    print("🔍 Searching for Amazon SEC filings...")
    response = queryApi.get_filings(search_query)
    
    if response.get("filings"):
        print(f"✅ Found {len(response['filings'])} filings")
        
        filing = response["filings"][0]  # Get the most recent
        print(f"\n📄 Most Recent Filing:")
        print(f"Company: {filing.get('companyName', 'N/A')}")
        print(f"Form Type: {filing.get('formType', 'N/A')}")
        print(f"Filed Date: {filing.get('filedAt', 'N/A')[:10]}")
        print(f"Filing URL: {filing.get('linkToFilingDetails', 'N/A')}")
        
        # Test the financial parsing function
        filing_url = filing.get('linkToFilingDetails')
        if filing_url:
            print(f"\n💰 Testing financial parsing on: {filing_url}")
            
            # Import and test the parse function from tools
            import sys
            sys.path.append('.')
            
            # Create a mock session state
            class MockSessionState:
                def __init__(self):
                    self.configurations = {"sec_api_key": sec_api_key}
            
            # Import the tools and set up mock session state
            import utils.tools as tools
            tools.ss = MockSessionState()
            
            # Test the financial parsing
            financial_data = tools.parse_financial_statements(filing_url, "AMZN")
            
            if financial_data:
                print("✅ Financial data extracted:")
                for key, value in financial_data.items():
                    if isinstance(value, (int, float)) and 'millions' in key:
                        if value >= 1000:
                            billions = value / 1000
                            print(f"  {key.replace('_millions', '').replace('_', ' ').title()}: ${billions:,.1f} billion")
                        else:
                            print(f"  {key.replace('_millions', '').replace('_', ' ').title()}: ${value:,.0f} million")
                    else:
                        print(f"  {key}: {value}")
            else:
                print("❌ No financial data extracted")
                
    else:
        print("❌ No filings found")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("Test complete!")
