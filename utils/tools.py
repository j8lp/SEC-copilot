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

model = ChatOpenAI(
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
    try:
        # Clean up the ticker symbol
        ticker = ticker.strip().upper()
        
        # Create ticker object
        stock_info = yf.Ticker(ticker)
        
        # Get current price - try multiple methods
        current_price = None
        
        # Method 1: Try info['currentPrice']
        try:
            current_price = stock_info.info.get("currentPrice")
        except:
            pass
        
        # Method 2: Try info['regularMarketPrice']
        if not current_price:
            try:
                current_price = stock_info.info.get("regularMarketPrice")
            except:
                pass
        
        # Method 3: Try history for most recent price
        if not current_price:
            try:
                hist = stock_info.history(period="1d")
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
            except:
                pass
        
        if current_price:
            # Get company name for confirmation
            company_name = stock_info.info.get("longName", ticker)
            return f"The current price of {company_name} ({ticker}) is USD ${current_price:.2f}"
        else:
            return f"Unable to retrieve current price for ticker symbol {ticker}. Please verify the ticker symbol is correct."
            
    except Exception as e:
        copilot_logger.error(f"Error getting stock price for {ticker}: {str(e)}")
        return f"An error occurred while retrieving the stock price for {ticker}. Please try again or verify the ticker symbol."


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

