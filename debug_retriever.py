"""Debug the live retriever function output"""
import os
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Mock session state for testing
class MockSessionState:
    def __init__(self):
        self.configurations = {
            "sec_api_key": os.getenv('SEC_API_KEY'),
            "openai_api_key": os.getenv('OPENAI_API_KEY')
        }
        self.stock_price_cache = {}
        self.error_message = None
        self.messages = []
    
    def __contains__(self, key):
        return hasattr(self, key)
    
    def __getitem__(self, key):
        return getattr(self, key)
    
    def __setitem__(self, key, value):
        setattr(self, key, value)
    
    def __delitem__(self, key):
        if hasattr(self, key):
            delattr(self, key)


# Set up mock environment
st.session_state = MockSessionState()

# Import the retriever function
from utils.tools import retriever

print("Testing retriever function with exact query...")
print("=" * 50)

try:
    # Test with the exact query from the app
    query = "Show me the financial statements for Amazon"
    
    print(f"Query: {query}")
    print("\nCalling retriever function...")
    
    result = retriever(query)
    
    print(f"\nResult length: {len(result)} characters")
    print(f"\nResult:")
    print("=" * 40)
    print(result)
    print("=" * 40)
    
    # Check if financial data is in the result
    has_numbers = any(word in result for word in ['$', 'billion', 'million', 'Revenue', 'Net Income'])
    has_url = 'sec.gov' in result.lower()
    
    print(f"\nAnalysis:")
    print(f"Contains financial numbers: {has_numbers}")
    print(f"Contains SEC URL: {has_url}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("Test complete!")
