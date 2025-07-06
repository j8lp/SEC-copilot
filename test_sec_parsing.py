"""Test SEC API responses without Streamlit dependencies"""
import os
from sec_api import QueryApi, FullTextSearchApi
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("Testing SEC API Filing Parsing...")
print("=" * 50)

try:
    # Initialize SEC API
    sec_api_key = os.getenv('SEC_API_KEY')
    if not sec_api_key:
        print("❌ SEC API key not found")
        exit(1)
    
    queryApi = QueryApi(api_key=sec_api_key)
    fullTextApi = FullTextSearchApi(api_key=sec_api_key)
    
    # Test 1: Get Amazon's latest filings
    print("🔍 Test 1: Getting Amazon's latest SEC filings...")
    search_query = {
        "query": 'ticker:AMZN AND formType:("10-K" OR "10-Q")',
        "from": "0",
        "size": "2",
        "sort": [{"filedAt": {"order": "desc"}}]
    }
    
    response = queryApi.get_filings(search_query)
    
    if response.get("filings"):
        print(f"✅ Found {len(response['filings'])} filings")
        
        for i, filing in enumerate(response["filings"]):
            print(f"\n📄 Filing {i+1}:")
            print(f"Company: {filing.get('companyName', 'N/A')}")
            print(f"Ticker: {filing.get('ticker', 'N/A')}")
            print(f"Form Type: {filing.get('formType', 'N/A')}")
            print(f"Filed Date: {filing.get('filedAt', 'N/A')[:10]}")
            print(f"Period: {filing.get('periodOfReport', 'N/A')}")
            print(f"Fiscal Year: {filing.get('fiscalYear', 'N/A')}")
            print(f"Description: {filing.get('description', 'N/A')}")
            print(f"Filing URL: {filing.get('linkToFilingDetails', 'N/A')}")
            print(f"Text URL: {filing.get('linkToTxt', 'N/A')}")
            print(f"HTML URL: {filing.get('linkToHtml', 'N/A')}")
    else:
        print("❌ No filings found")
    
    # Test 2: Full-text search for financial terms
    print(f"\n🔍 Test 2: Full-text search for 'revenue' in Amazon filings...")
    try:
        full_text_query = {
            "query": 'ticker:AMZN AND "revenue"',
            "formTypes": ["10-K", "10-Q"],
            "startDate": "2023-01-01",
            "endDate": "2024-12-31"
        }
        
        full_text_response = fullTextApi.get_filings(full_text_query)
        
        if full_text_response.get("filings"):
            print(f"✅ Found {len(full_text_response['filings'])} filings with revenue information")
            
            filing = full_text_response["filings"][0]
            print(f"📄 Most recent match:")
            print(f"Company: {filing.get('companyName', 'N/A')}")
            print(f"Form: {filing.get('formType', 'N/A')}")
            print(f"Filed: {filing.get('filedAt', 'N/A')[:10]}")
            print(f"URL: {filing.get('linkToFilingDetails', 'N/A')}")
        else:
            print("❌ No full-text matches found")
            
    except Exception as e:
        print(f"❌ Full-text search error: {e}")
    
    # Test 3: Try to extract specific financial data patterns
    print(f"\n🔍 Test 3: Testing different search strategies...")
    
    # Search for specific financial statement terms
    financial_terms = ["net sales", "total revenue", "net income", "total assets"]
    
    for term in financial_terms[:2]:  # Test first 2 terms
        try:
            term_query = {
                "query": f'ticker:AMZN AND "{term}"',
                "formTypes": ["10-K"],
                "startDate": "2023-01-01",
                "endDate": "2024-12-31"
            }
            
            term_response = fullTextApi.get_filings(term_query)
            
            if term_response.get("filings"):
                print(f"✅ Found filings mentioning '{term}': {len(term_response['filings'])} results")
            else:
                print(f"❌ No filings found for '{term}'")
                
        except Exception as e:
            print(f"❌ Error searching for '{term}': {e}")
        
except Exception as e:
    print(f"❌ Main error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("Test complete!")
print("\nNext steps:")
print("1. The SEC API provides metadata and links to filings")
print("2. Actual financial data is in the filing documents")
print("3. Full-text search can find filings containing specific terms")
print("4. To get exact numbers, we'd need to parse the filing documents")
print("5. Direct document parsing is challenging due to SEC access restrictions")
