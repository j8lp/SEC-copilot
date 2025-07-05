import streamlit as st
from sec_api import QueryApi, FullTextSearchApi
import requests
from bs4 import BeautifulSoup

import logging
copilot_logger = logging.getLogger("copilot")
copilot_logger.setLevel(logging.ERROR)

from langchain.agents import Tool
from langchain.tools import tool

from langchain_openai import ChatOpenAI

from langchain_core.runnables import RunnableParallel
from langchain_core.output_parsers import StrOutputParser

from langchain_community.tools import DuckDuckGoSearchRun
from langchain.tools import tool

@tool
def robust_search_tool(query: str) -> str:
    """Search the web for information. Handles rate limiting gracefully."""
    import time
    import random
    from datetime import datetime
    
    try:
        # Add delay to avoid rate limiting
        time.sleep(random.uniform(1, 3))
        
        # Try DuckDuckGo search
        ddg_search = DuckDuckGoSearchRun()
        results = ddg_search.run(query)
        return results
        
    except Exception as e:
        error_msg = str(e).lower()
        
        if "ratelimit" in error_msg or "rate limit" in error_msg:
            return (
                f"⚠️ Web search is currently rate-limited. "
                f"This is a temporary limitation of the free search API.\n\n"
                f"🔍 For the latest news about your query '{query}', you can manually check:\n"
                f"• Google News: https://news.google.com/search?q={query.replace(' ', '+')}\n"
                f"• Yahoo Finance News: https://finance.yahoo.com/news/\n"
                f"• Reuters: https://www.reuters.com/\n"
                f"• Bloomberg: https://www.bloomberg.com/\n\n"
                f"💡 The rate limiting usually resolves within 10-15 minutes. "
                f"You can ask about SEC filings instead, which don't have this limitation!"
            )
        else:
            return (
                f"I encountered an error while searching for '{query}'. "
                f"This might be due to connectivity issues or API limitations.\n\n"
                f"🔍 You can manually search for this information at:\n"
                f"• Google: https://www.google.com/search?q={query.replace(' ', '+')}\n"
                f"• DuckDuckGo: https://duckduckgo.com/?q={query.replace(' ', '+')}\n\n"
                f"Please try again later, or ask about SEC filings which I can search directly!"
            )

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
        
        # Initialize cache if not exists (handle session state issues)
        try:
            if 'stock_price_cache' not in ss:
                ss.stock_price_cache = {}
                ss.stock_price_cache_time = {}
                
            # Check cache first (cache for 5 minutes)
            if ticker in ss.stock_price_cache:
                cache_time = ss.stock_price_cache_time.get(ticker, datetime.min)
                if datetime.now() - cache_time < timedelta(minutes=5):
                    return ss.stock_price_cache[ticker]
        except Exception:
            # If session state fails, proceed without caching
            pass
        
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
            # Cache the result if session state is available
            try:
                ss.stock_price_cache[ticker] = result
                ss.stock_price_cache_time[ticker] = datetime.now()
            except Exception:
                # If session state fails, proceed without caching
                pass
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


def parse_financial_statements(filing_url, ticker):
    """
    Parse financial statements from SEC filing URL.
    Extracts key financial metrics from 10-K and 10-Q filings.
    """
    import requests
    import re
    from bs4 import BeautifulSoup
    import time
    
    try:
        headers = {
            'User-Agent': 'SEC Financial Parser 1.0 (research@example.com)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
        }
        
        # Add delay to be respectful to SEC servers
        time.sleep(2)
        
        response = requests.get(filing_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        text_content = soup.get_text()
        
        # Financial data patterns
        financial_data = {}
        
        # Revenue patterns
        revenue_patterns = [
            r'Net sales[\s\$]*(\d{1,3}(?:,\d{3})*)',
            r'Total net sales[\s\$]*(\d{1,3}(?:,\d{3})*)',
            r'Revenue[\s\$]*(\d{1,3}(?:,\d{3})*)',
            r'Total revenue[\s\$]*(\d{1,3}(?:,\d{3})*)',
        ]
        
        for pattern in revenue_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            if matches:
                amounts = [int(match.replace(',', '')) for match in matches]
                if amounts:
                    financial_data['revenue_millions'] = max(amounts)
                    break
        
        # Net income patterns
        income_patterns = [
            r'Net income[\s\$]*(\d{1,3}(?:,\d{3})*)',
            r'Net earnings[\s\$]*(\d{1,3}(?:,\d{3})*)',
        ]
        
        for pattern in income_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            if matches:
                amounts = [int(match.replace(',', '')) for match in matches]
                if amounts:
                    financial_data['net_income_millions'] = max(amounts)
                    break
        
        # Total assets pattern
        assets_patterns = [
            r'Total assets[\s\$]*(\d{1,3}(?:,\d{3})*)',
        ]
        
        for pattern in assets_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            if matches:
                amounts = [int(match.replace(',', '')) for match in matches]
                if amounts:
                    financial_data['total_assets_millions'] = max(amounts)
                    break
        
        # Cash and equivalents
        cash_patterns = [
            r'Cash and cash equivalents[\s\$]*(\d{1,3}(?:,\d{3})*)',
        ]
        
        for pattern in cash_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            if matches:
                amounts = [int(match.replace(',', '')) for match in matches]
                if amounts:
                    financial_data['cash_millions'] = max(amounts)
                    break
        
        return financial_data
        
    except Exception as e:
        copilot_logger.error(f"Error parsing financial statements for {ticker}: {str(e)}")
        return {}


def get_financial_data_from_sec_api(queryApi, ticker, form_type="10-K"):
    """
    Use SEC API to get more detailed financial information.
    This approach uses the SEC API's structured data capabilities.
    """
    try:
        # Search for specific financial data sections
        search_query = {
            "query": f'ticker:{ticker} AND formType:"{form_type}"',
            "from": "0",
            "size": "1",
            "sort": [{"filedAt": {"order": "desc"}}]
        }
        
        response = queryApi.get_filings(search_query)
        
        if response.get("filings"):
            filing = response["filings"][0]
            
            # Extract key information from the filing
            financial_summary = {
                'company_name': filing.get('companyName', 'Unknown'),
                'ticker': filing.get('ticker', ticker),
                'form_type': filing.get('formType', form_type),
                'filing_date': filing.get('filedAt', 'Unknown')[:10],
                'period_end': filing.get('periodOfReport', 'Unknown'),
                'fiscal_year': filing.get('fiscalYear', 'Unknown'),
                'fiscal_quarter': filing.get('fiscalQuarter', 'Unknown'),
                'filing_url': filing.get('linkToFilingDetails', 'N/A'),
                'html_url': filing.get('linkToHtml', 'N/A'),
                'document_description': filing.get('description', 'N/A')
            }
            
            return financial_summary
            
    except Exception as e:
        copilot_logger.error(f"Error getting financial data from SEC API for {ticker}: {str(e)}")
        return {}


def extract_income_statement_data(table):
    """Extract revenue, expenses, and net income from income statement table."""
    data = {}
    
    try:
        rows = table.find_all('tr')
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                row_text = cells[0].get_text(strip=True).upper()
                
                # Look for revenue patterns
                if any(keyword in row_text for keyword in ['TOTAL REVENUE', 'NET SALES', 'REVENUE', 'TOTAL NET SALES']):
                    values = extract_financial_values(cells[1:])
                    if values:
                        data['revenue'] = values[0]
                
                # Look for net income patterns
                if any(keyword in row_text for keyword in ['NET INCOME', 'NET EARNINGS', 'NET LOSS']):
                    values = extract_financial_values(cells[1:])
                    if values:
                        data['net_income'] = values[0]
                
                # Look for gross profit
                if any(keyword in row_text for keyword in ['GROSS PROFIT', 'GROSS INCOME']):
                    values = extract_financial_values(cells[1:])
                    if values:
                        data['gross_profit'] = values[0]
                
                # Look for operating expenses
                if any(keyword in row_text for keyword in ['OPERATING EXPENSES', 'TOTAL OPERATING EXPENSES']):
                    values = extract_financial_values(cells[1:])
                    if values:
                        data['operating_expenses'] = values[0]
    
    except Exception as e:
        copilot_logger.error(f"Error extracting income statement data: {str(e)}")
    
    return data


def extract_balance_sheet_data(table):
    """Extract assets, liabilities, and equity from balance sheet table."""
    data = {}
    
    try:
        rows = table.find_all('tr')
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                row_text = cells[0].get_text(strip=True).upper()
                
                # Look for total assets
                if any(keyword in row_text for keyword in ['TOTAL ASSETS', 'TOTAL CURRENT ASSETS']):
                    values = extract_financial_values(cells[1:])
                    if values:
                        data['total_assets'] = values[0]
                
                # Look for total liabilities
                if any(keyword in row_text for keyword in ['TOTAL LIABILITIES', 'TOTAL CURRENT LIABILITIES']):
                    values = extract_financial_values(cells[1:])
                    if values:
                        data['total_liabilities'] = values[0]
                
                # Look for shareholders' equity
                if any(keyword in row_text for keyword in ['STOCKHOLDERS EQUITY', 'SHAREHOLDERS EQUITY', 'TOTAL EQUITY']):
                    values = extract_financial_values(cells[1:])
                    if values:
                        data['stockholders_equity'] = values[0]
                
                # Look for cash and equivalents
                if any(keyword in row_text for keyword in ['CASH AND CASH EQUIVALENTS', 'CASH AND EQUIVALENTS']):
                    values = extract_financial_values(cells[1:])
                    if values:
                        data['cash_and_equivalents'] = values[0]
    
    except Exception as e:
        copilot_logger.error(f"Error extracting balance sheet data: {str(e)}")
    
    return data


def extract_cash_flow_data(table):
    """Extract cash flow data from cash flow statement table."""
    data = {}
    
    try:
        rows = table.find_all('tr')
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                row_text = cells[0].get_text(strip=True).upper()
                
                # Look for operating cash flow
                if any(keyword in row_text for keyword in ['NET CASH PROVIDED BY OPERATING', 'CASH FROM OPERATING']):
                    values = extract_financial_values(cells[1:])
                    if values:
                        data['operating_cash_flow'] = values[0]
                
                # Look for investing cash flow
                if any(keyword in row_text for keyword in ['NET CASH USED IN INVESTING', 'CASH FROM INVESTING']):
                    values = extract_financial_values(cells[1:])
                    if values:
                        data['investing_cash_flow'] = values[0]
                
                # Look for financing cash flow
                if any(keyword in row_text for keyword in ['NET CASH PROVIDED BY FINANCING', 'CASH FROM FINANCING']):
                    values = extract_financial_values(cells[1:])
                    if values:
                        data['financing_cash_flow'] = values[0]
    
    except Exception as e:
        copilot_logger.error(f"Error extracting cash flow data: {str(e)}")
    
    return data


def extract_financial_values(cells):
    """Extract financial values from table cells, handling various formats."""
    import re
    
    values = []
    
    for cell in cells:
        cell_text = cell.get_text(strip=True)
        
        # Remove common formatting characters
        clean_text = re.sub(r'[,$\s]', '', cell_text)
        
        # Look for numbers (including negative numbers in parentheses)
        number_match = re.search(r'^\(?(\d+(?:\.\d+)?)\)?$', clean_text)
        if number_match:
            value = float(number_match.group(1))
            # Handle negative numbers in parentheses
            if cell_text.strip().startswith('(') and cell_text.strip().endswith(')'):
                value = -value
            values.append(value)
    
    return values


def retriever(query):
    """
    Retrieves SEC filings using SEC-API and processes them to answer questions.
    Uses both filing metadata and full-text search for comprehensive results.
    Now includes financial statement parsing for detailed data extraction.
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
            for filing in response["filings"][:2]:  # Limit to 2 recent filings
                filing_info = f"""
                SEC Filing Found:
                Company: {filing.get('companyName', 'Unknown')}
                Ticker: {filing.get('ticker', 'N/A')}
                Form Type: {filing.get('formType', 'Unknown')}
                Filed: {filing.get('filedAt', 'Unknown')[:10]}
                Period End: {filing.get('periodOfReport', 'Unknown')}
                📄 Filing URL: {filing.get('linkToFilingDetails', 'Not available')}
                """
                
                # Parse financial statements from the filing
                filing_url = filing.get('linkToFilingDetails')
                ticker_symbol = filing.get('ticker', possible_ticker)
                
                if filing_url and ticker_symbol:
                    financial_data = parse_financial_statements(filing_url, ticker_symbol)
                    
                    if financial_data:
                        filing_info += "\n=== EXTRACTED FINANCIAL DATA ===\n"
                        for key, value in financial_data.items():
                            if isinstance(value, (int, float)) and 'millions' in key:
                                # Format as millions/billions with better spacing
                                if value >= 1000:
                                    billions = value / 1000
                                    filing_info += f"• {key.replace('_millions', '').replace('_', ' ').title()}: ${billions:,.1f} billion\n"
                                else:
                                    filing_info += f"• {key.replace('_millions', '').replace('_', ' ').title()}: ${value:,.0f} million\n"
                            else:
                                filing_info += f"• {key.replace('_', ' ').title()}: {value}\n"
                        filing_info += f"\n📄 Source: {filing.get('linkToFilingDetails', 'URL not available')}\n"
                        filing_info += "=== END FINANCIAL DATA ===\n"
                    else:
                        filing_info += f"""
                        
                This {filing.get('formType', 'Unknown')} filing contains comprehensive financial information.
                Financial statement parsing was attempted but no data was extracted.
                You can access the complete filing at: {filing.get('linkToFilingDetails', 'URL not available')}
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


search_tool = robust_search_tool

