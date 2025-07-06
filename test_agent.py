"""Test the ReAct agent directly"""
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

# Import required components
from utils.tools import retrieval_tool, get_current_stock_price
from utils.prompts import react_prompt
from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor

print("Testing ReAct agent directly...")
print("=" * 50)

try:
    # Set up the agent exactly like in chat/main.py
    model = ChatOpenAI(
        model="gpt-3.5-turbo-16k", 
        openai_api_key=st.session_state.configurations["openai_api_key"]
    )
    
    tools = [get_current_stock_price, retrieval_tool]
    
    agent = create_react_agent(
        llm=model,
        tools=tools,
        prompt=react_prompt
    )
    
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        handle_parsing_errors=True,
        verbose=True  # Enable verbose output to see what's happening
    )
    
    # Test query
    query = "Show me the financial statements for Amazon"
    
    print(f"Query: {query}")
    print("\nExecuting agent...")
    
    result = agent_executor.invoke({
        "input": query,
        "chat_history": ""
    })
    
    print(f"\nAgent result:")
    print("=" * 40)
    print(result["output"])
    print("=" * 40)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("Test complete!")
