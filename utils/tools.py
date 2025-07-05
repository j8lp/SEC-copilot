import streamlit as st
from sec_api import QueryApi, FullTextSearchApi

import logging
copilot_logger = logging.getLogger("copilot")
copilot_logger.setLevel(logging.ERROR)

from langchain.agents import Tool
from langchain.tools import tool

from langchain_openai import ChatOpenAI

from langchain_core.runnables import RunnableParallel
from langchain_core.output_parsers import StrOutputParser

from langchain_community.tools import DuckDuckGoSearchRun

from pydantic.v1 import BaseModel, Field

import yfinance as yf

from utils.prompts import prompt

ss = st.session_state

# Cache for stock prices to avoid rate limiting
if 'stock_price_cache' not in ss:
    ss.stock_price_cache = {}
    ss.stock_price_cache_time = {}

def get_openai_model():
    """Get initialized OpenAI model with API key from session state."""
    return ChatOpenAI(
        model="gpt-3.5-turbo-16k", 
        openai_api_key=ss.configurations["openai_api_key"]
    )


class CurrentStockPriceInput(BaseModel):
    symbol: str = Field(
        ..., 
        description="The ticker symbol for the company whose stock price is to be checked."
    )


@tool(args_schema=CurrentStockPriceInput)
def get_current_stock_price(ticker: str) -> str:
    """Call this function with only a company's ticker symbol, to get the current stock price for the company."""
    import time
    import random
    from datetime import datetime, timedelta
    
    try:
        # Clean up the ticker symbol
        ticker = ticker.strip().upper()
        
        # Check cache first (cache for 5 minutes)
        if ticker in ss.stock_price_cache:
            cache_time = ss.stock_price_cache_time.get(ticker, datetime.min)
            if datetime.now() - cache_time < timedelta(minutes=5):
                return ss.stock_price_cache[ticker]
        
        # Add a small random delay to avoid rate limiting
        time.sleep(random.uniform(0.5, 1.5))
        
        # Create ticker object
        stock_info = yf.Ticker(ticker)
        
        # Get current price - try multiple methods with rate limit handling
        current_price = None
        company_name = ticker
        
        # Method 1: Try history for most recent price (most reliable)
        try:
            hist = stock_info.history(period="1d", interval="1d")
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
        except Exception as e:
            if "429" in str(e) or "Too Many Requests" in str(e):
                rate_limit_msg = (
                    f"Yahoo Finance is currently rate-limiting requests. "
                    f"Please try again in a few minutes. For {ticker}, "
                    f"you can check the price manually at "
                    f"https://finance.yahoo.com/quote/{ticker}"
                )
                return rate_limit_msg
        
        # Method 2: Try basic info (if history fails)
        if not current_price:
            try:
                basic_info = stock_info.basic_info
                if basic_info and 'previousClose' in basic_info:
                    current_price = basic_info['previousClose']
                    company_name = basic_info.get('longName', ticker)
            except Exception as e:
                if "429" in str(e) or "Too Many Requests" in str(e):
                    rate_limit_msg = (
                        f"Yahoo Finance is currently rate-limiting requests. "
                        f"Please try again in a few minutes. For {ticker}, "
                        f"you can check the price manually at "
                        f"https://finance.yahoo.com/quote/{ticker}"
                    )
                    return rate_limit_msg
        
        if current_price and current_price > 0:
            result = (
                f"The current price of {company_name} ({ticker}) is "
                f"USD ${current_price:.2f}. Note: Data may be delayed "
                f"by up to 20 minutes."
            )
            # Cache the result
            ss.stock_price_cache[ticker] = result
            ss.stock_price_cache_time[ticker] = datetime.now()
            return result
        else:
            return (
                f"Unable to retrieve current price for {ticker}. "
                f"This might be due to:\n"
                f"1. Rate limiting from Yahoo Finance\n"
                f"2. Invalid ticker symbol\n"
                f"3. Market is closed\n\n"
                f"Please verify the ticker symbol or try again later. "
                f"You can also check manually at "
                f"https://finance.yahoo.com/quote/{ticker}"
            )
            
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "Too Many Requests" in error_msg:
            return (
                f"Yahoo Finance is currently rate-limiting requests. "
                f"Please try again in a few minutes. For {ticker}, "
                f"you can check the price manually at "
                f"https://finance.yahoo.com/quote/{ticker}"
            )
        else:
            copilot_logger.error(f"Error getting stock price for {ticker}: {error_msg}")
            return (
                f"An error occurred while retrieving the stock price for {ticker}. "
                f"Error: {error_msg[:100]}... "
                f"Please try again later or check manually at "
                f"https://finance.yahoo.com/quote/{ticker}"
            )


def handle_sec_api_errors(error_message: str):
    """Handles errors that occur during call to SEC API endpoint."""
    copilot_logger.error(f"SEC API error: {error_message}")
    ss.error_message = "An error occurred while retrieving SEC filings."


def retriever(query):
    """
    Retrieves SEC filings using SEC-API and processes them to answer questions.
    Uses both filing metadata and full-text search for comprehensive results.
    """
    try:
        # Initialize SEC API clients
        queryApi = QueryApi(api_key=ss.configurations["sec_api_key"])
        fullTextApi = FullTextSearchApi(api_key=ss.configurations["sec_api_key"])
        
        # Extract company ticker or name from query if possible
        # This is a simple approach - could be enhanced with NLP
        query_upper = query.upper()
        possible_ticker = None
        
        # Company name to ticker mapping for better detection
        company_mappings = {
            'APPLE': 'AAPL',
            'MICROSOFT': 'MSFT', 
            'GOOGLE': 'GOOGL',
            'ALPHABET': 'GOOGL',
            'AMAZON': 'AMZN',
            'TESLA': 'TSLA',
            'META': 'META',
            'FACEBOOK': 'META',
            'NVIDIA': 'NVDA',
            'BERKSHIRE': 'BRK',
            'JPM': 'JPM',
            'JP MORGAN': 'JPM',
            'VISA': 'V'
        }
        
        # First check for company names
        for company_name, ticker in company_mappings.items():
            if company_name in query_upper:
                possible_ticker = ticker
                break
        
        # If no company name found, check for direct ticker matches
        if not possible_ticker:
            tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'BRK', 'JPM', 'V']
            for ticker in tickers:
                # Use word boundaries to avoid partial matches
                import re
                if re.search(r'\b' + ticker + r'\b', query_upper):
                    possible_ticker = ticker
                    break
        
        texts = []
        
        # Search 1: Filing metadata search
        if possible_ticker:
            search_query = {
                "query": f'ticker:{possible_ticker} AND formType:("10-K" OR "10-Q")',
                "from": "0",
                "size": "5",
                "sort": [{"filedAt": {"order": "desc"}}]
            }
        else:
            # Generic search if no ticker identified
            search_query = {
                "query": f'formType:("10-K" OR "10-Q") AND companyName:{query}',
                "from": "0", 
                "size": "5",
                "sort": [{"filedAt": {"order": "desc"}}]
            }
        
        # Get filings metadata
        response = queryApi.get_filings(search_query)
        
        if response.get("filings"):
            for filing in response["filings"][:3]:  # Limit to 3 recent filings
                filing_info = f"""
                Company: {filing.get('companyName', 'Unknown')}
                Ticker: {filing.get('ticker', 'N/A')}
                Form Type: {filing.get('formType', 'Unknown')}
                Filed: {filing.get('filedAt', 'Unknown')[:10]}
                Period: {filing.get('periodOfReport', 'Unknown')}
                Description: {filing.get('description', 'Unknown')}
                """
                texts.append(filing_info)
        
        # Search 2: Full-text search for more detailed content
        try:
            full_text_query = {
                "query": f'"{query}"',
                "formTypes": ["10-K", "10-Q"],
                "startDate": "2022-01-01",  # Last 2 years
                "endDate": "2024-12-31"
            }
            
            full_text_response = fullTextApi.get_filings(full_text_query)
            
            if full_text_response.get("filings"):
                for filing in full_text_response["filings"][:2]:  # Add 2 more
                    filing_info = f"""
                    Full-text Match:
                    Company: {filing.get('companyName', 'Unknown')}
                    Form: {filing.get('formType', 'Unknown')}
                    Filed: {filing.get('filedAt', 'Unknown')[:10]}
                    Relevance: High text match for "{query}"
                    """
                    texts.append(filing_info)
        
        except Exception as e:
            # If full-text search fails, continue with metadata search only
            copilot_logger.info(f"Full-text search failed: {str(e)}")
        
        if not texts:
            return (
                "No relevant SEC filings found for your query. "
                "Please try a different search term, company name, or ticker symbol."
            )

        # Use LangChain to process the query with the SEC filing context
        model = get_openai_model()
        chain = RunnableParallel({
            "question": lambda x: x["question"],
            "context": lambda x: x["context"]
        }) | prompt | model | StrOutputParser()

        answer = chain.invoke({
            "question": query,
            "context": texts
        })
        
        return answer
        
    except Exception as e:
        handle_sec_api_errors(str(e))
        return f"An error occurred while retrieving SEC data: {str(e)}"


retrieval_tool = Tool(
    name="SEC API Filing Search",
    func=retriever,
    description=(
        "Use this tool when answering questions that relate to a company's "
        "SEC filings, financials and/or spending patterns. Searches 10-K "
        "and 10-Q filings from the SEC database."
    ),
)


search_tool = DuckDuckGoSearchRun()

