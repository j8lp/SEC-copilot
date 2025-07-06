"""Simple test of SEC API"""
import os
from dotenv import load_dotenv
from sec_api import QueryApi

load_dotenv()

try:
    api_key = os.getenv('SEC_API_KEY')
    print(f"API Key loaded: {'Yes' if api_key else 'No'}")
    
    if api_key:
        queryApi = QueryApi(api_key=api_key)
        
        search_query = {
            "query": 'ticker:AMZN AND formType:"10-K"',
            "from": "0",
            "size": "1"
        }
        
        print("Searching for Amazon 10-K filings...")
        response = queryApi.get_filings(search_query)
        
        print(f"Response received: {type(response)}")
        print(f"Number of filings: {len(response.get('filings', []))}")
        
        if response.get('filings'):
            filing = response['filings'][0]
            print(f"Company: {filing.get('companyName')}")
            print(f"Form: {filing.get('formType')}")
            print(f"Filed: {filing.get('filedAt')}")
            print(f"URL: {filing.get('linkToFilingDetails')}")
    else:
        print("No SEC API key found")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
