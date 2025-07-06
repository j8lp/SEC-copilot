"""Detailed SEC API test to see what data is available"""
import os
from sec_api import QueryApi
from dotenv import load_dotenv

load_dotenv()

print("Testing SEC API data extraction...")
print("=" * 50)

try:
    queryApi = QueryApi(api_key=os.getenv('SEC_API_KEY'))
    
    # Test query for Amazon's latest 10-K
    search_query = {
        "query": 'ticker:AMZN AND formType:"10-K"',
        "from": "0",
        "size": "1",
        "sort": [{"filedAt": {"order": "desc"}}]
    }
    
    print("🔍 Searching for Amazon's latest 10-K filing...")
    response = queryApi.get_filings(search_query)
    
    if response.get("filings"):
        filing = response["filings"][0]
        print(f"✅ Found filing: {filing.get('formType')} filed on {filing.get('filedAt')}")
        
        # Show all available fields
        print("\nAvailable fields in filing:")
        for key, value in filing.items():
            if isinstance(value, (str, int, float)):
                print(f"  {key}: {str(value)[:100]}...")
            else:
                print(f"  {key}: {type(value)} - {str(value)[:50]}...")
        
        # Check if we have links to actual filing content
        print(f"\nFiling Links:")
        for link_key in ['linkToTxt', 'linkToHtml', 'linkToXbrl', 'linkToFilingDetails']:
            if link_key in filing:
                print(f"  {link_key}: {filing[link_key]}")
    else:
        print("❌ No filings found")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("Test complete!")
