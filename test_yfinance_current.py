"""Test the yfinance stock price tool"""
import sys
import os
from utils.tools import get_current_stock_price

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Testing YFinance Stock Price Tool...")
print("=" * 50)

# Test with a few different stocks
test_stocks = ["AAPL", "NVDA", "MSFT"]

for ticker in test_stocks:
    print(f"🔍 Testing stock price for: {ticker}")
    try:
        result = get_current_stock_price(ticker)
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
    print("-" * 30)

print("=" * 50)
print("Test complete!")
