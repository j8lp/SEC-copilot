"""Test the full chat pipeline"""
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
    
    def __delitem__(self, key):
        if hasattr(self, key):
            delattr(self, key)

# Set up mock environment
st.session_state = MockSessionState()

# Import the get_response function
from chat.main import get_response

print("Testing full chat pipeline...")
print("=" * 50)

try:
    # Test with the same query that would be used in the app
    query = "Show me the financial statements for Amazon"
    configurations = st.session_state.configurations
    chat_history = []
    
    print(f"Query: {query}")
    print("\nCalling get_response function...")
    
    answer, updated_chat_history = get_response(query, configurations, chat_history)
    
    print(f"\nAnswer type: {type(answer)}")
    print(f"Answer: {answer}")
    print(f"\nChat history updated: {len(updated_chat_history)} entries")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("Test complete!")
