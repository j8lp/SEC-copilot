"""Simple test of SEC API without Streamlit dependencies"""
import os
from sec_api import QueryApi
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("Testing SEC API responses...")
print("=" * 50)

try:
    # Initialize SEC API
    sec_api_key = os.getenv('SEC_API_KEY')
    if not sec_api_key:
        print("❌ SEC API key not found in environment variables")
        exit(1)
    
    queryApi = QueryApi(api_key=sec_api_key)
    
    # Test query for Amazon
    search_query = {
        "query": 'ticker:AMZN AND formType:("10-K" OR "10-Q")',
        "from": "0",
        "size": "2",
        "sort": [{"filedAt": {"order": "desc"}}]
    }
    
    print("🔍 Searching for Amazon SEC filings...")
    
    # Add timeout to prevent hanging
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError("Request timed out")
    
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(10)  # 10 second timeout
    
    try:
        response = queryApi.get_filings(search_query)
        signal.alarm(0)  # Cancel the alarm
    except TimeoutError:
        print("❌ Request timed out after 10 seconds")
        exit(1)
    
    if response.get("filings"):
        print(f"✅ Found {len(response['filings'])} filings")
        
        for i, filing in enumerate(response["filings"][:1]):  # Just look at first one
            print(f"\n📄 Filing {i+1}:")
            print(f"Company: {filing.get('companyName', 'N/A')}")
            print(f"Ticker: {filing.get('ticker', 'N/A')}")
            print(f"Form Type: {filing.get('formType', 'N/A')}")
            print(f"Filed At: {filing.get('filedAt', 'N/A')}")
            print(f"Period: {filing.get('periodOfReport', 'N/A')}")
            print(f"Filing URL: {filing.get('linkToFilingDetails', 'N/A')}")
            
            # Show some other interesting fields
            print(f"\nOther fields:")
            for key, value in filing.items():
                if key in ['linkToTxt', 'linkToHtml', 'linkToXbrl', 'acceptanceDateTime', 'cik']:
                    print(f"  {key}: {value}")
    else:
        print("❌ No filings found")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("Test complete!")
