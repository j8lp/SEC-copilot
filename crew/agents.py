import streamlit as st

# import langchain
# langchain.debug=True

from crewai import Agent

from utils.tools import (
    retrieval_tool, search_tool, 
    get_current_stock_price
)

from langchain_openai import ChatOpenAI

# from dotenv import load_dotenv
# load_dotenv()

# openai_api_key = os.environ.get("OPENAI_API_KEY")
# kay_api_key = os.environ.get("KAY_API_KEY")

ss = st.session_state

def get_openai_model():
    """Get initialized OpenAI model with API key from session state."""
    return ChatOpenAI(
        model="gpt-3.5-turbo-16k", 
        openai_api_key=ss.configurations["openai_api_key"]
    )

class InvestmentAgents():

    def fillings_researcher(self):
        return Agent(
            role="SEC Fillings Research Expert",
            goal="Find and analyze financial information from company SEC filings to provide detailed, specific financial data and insights.",
            backstory="""An expert financial analyst with deep expertise in reading and interpreting SEC filings.
            You excel at extracting specific financial data, numbers, and insights from 10-K and 10-Q forms.
            You always provide concrete financial figures, revenue numbers, expense breakdowns, and spending patterns.
            You never just say you found information - you always share the actual data and numbers.""",
            tools=[retrieval_tool],
            llm=get_openai_model(),
            allow_delegation=False,
            # verbose=True
        )
    
    def market_trader(self):
        return Agent(
            role="Stock Price Seeker",
            goal="Find the current stock price of a company.",
            backstory="An expert stock market trader able to find out the current stock price of a company.",
            tools=[get_current_stock_price],
            llm=get_openai_model(),
            allow_delegation=False,
            # verbose=True
        )

    def news_researcher(self):
        return Agent(
            role="News Research Expert",
            goal="Find most recent news headlines that can affect investment decisions.",
            backstory="""An expert news analyst. Your expertise lies in getting relevant 
            news articles from the internet on a specific company.""",
            tools=[search_tool],
            llm=get_openai_model(),
            # verbose=True
        )
    
    def report_writer(self):
        return Agent(
            role="Report Writing Expert",
            goal="""Impress your customers with a robust company analysis.""",
            backstory="""An expert report writer, capable of writing financial articles for investors to highlights 
            key pieces of information to facilitate informed, data-driven investment decisions.""",
            llm=get_openai_model(),
            # verbose=True
        )
