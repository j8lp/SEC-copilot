"""Quick SEC API test"""
import os
from dotenv import load_dotenv
load_dotenv()

# Test if SEC API key is available
sec_api_key = os.getenv('SEC_API_KEY')
print(f"SEC API Key exists: {bool(sec_api_key)}")
print(f"SEC API Key length: {len(sec_api_key) if sec_api_key else 0}")

# Test basic SEC API import
try:
    from sec_api import QueryApi
    print("✅ SEC API import successful")
    
    # Test creating API instance
    queryApi = QueryApi(api_key=sec_api_key)
    print("✅ SEC API instance created")
    
    # Test simple query
    print("🔍 Testing simple query...")
    search_query = {
        "query": 'ticker:AAPL',
        "from": "0",
        "size": "1"
    }
    
    response = queryApi.get_filings(search_query)
    print(f"✅ Query successful, found {len(response.get('filings', []))} filings")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("Test complete!")
