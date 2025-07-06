"""Test the robust search tool to verify fallback behavior"""
import sys
import os
from utils.tools import robust_search_tool

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Testing Robust Search Tool...")
print("=" * 50)

# Test the robust search tool
query = "Apple stock news"
print(f"🔍 Testing robust search with query: '{query}'")
result = robust_search_tool(query)
print("Result:")
print(result)
print("=" * 50)
print("Test complete!")
