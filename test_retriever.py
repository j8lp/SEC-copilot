"""Test what the retriever function actually returns"""
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
    
    def __contains__(self, key):
        return hasattr(self, key)
    
    def __getitem__(self, key):
        return getattr(self, key)
    
    def __setitem__(self, key, value):
        setattr(self, key, value)

# Set up mock environment
st.session_state = MockSessionState()

# Import the retriever function
from utils.tools import retriever

print("Testing retriever function...")
print("=" * 50)

try:
    # Test with the same query that would be used in the app
    query = "Show me the financial statements for Amazon"
    
    print(f"Query: {query}")
    print("\nCalling retriever function...")
    
    result = retriever(query)
    
    print(f"\nResult length: {len(result)} characters")
    print(f"\nResult:\n{result}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("Test complete!")
