from crewai import Task

class InvestmentTasks():
    def fillings_research(self, agent, company):
        return Task(
            description=f"""Use the SEC API Filing Search tool to search for and analyze SEC filings for {company}.
Search for the most recent financial information from:
- Annual reports (10-K forms)
- Quarterly reports (10-Q forms)

When you receive SEC filing information, you MUST:
1. Extract and present specific financial data including:
   - Revenue figures and growth trends
   - Net income/profit numbers
   - Total assets and liabilities
   - Cash flow information
   - Key financial ratios and metrics
2. Mention the specific form types (10-K, 10-Q) and filing dates
3. Provide direct links to the actual SEC filings for complete details
4. If the tool doesn't return specific financial numbers, clearly state that 
   the user should refer to the full filing documents

DO NOT just say "the SEC API tool provided information" - you must extract and 
present the actual financial data that was returned.

{self.__tip_section()}

Your final answer MUST include specific financial data and numbers from the SEC filings.
If you cannot find specific financial figures in the tool results, clearly explain 
what information is available and direct the user to the filing URLs for complete data.""",
            agent=agent
        )
    
    def market_trade(self, agent, company):
        return Task(
            description=f"""Find the current stock price of {company},
            
            {self.__tip_section()}
            
            The input for your tool is only the ticker symbol for a given company. Do not add anything else asides the 
            ticker symbol to your input.
            
            Your final answer MUST expand on the spending patterns you're provided and also include the stock price of the company as well.""",
            agent=agent
        )

    def news_research(self, agent, company):
        return Task(
            description=f"""Collect and summarize news headlines for {company}, paying special
            attention to headlines regarding market sentiment, investor behaviour, upcoming events like earnings, etc. 
            
            {self.__tip_section()}
            
            Make sure the data you use is as recent as possible.
            
            Your final answer MUST include the spending patterns provided to you, contain the news headlines you found as well as the current stock price data you were 
            provided with.""",
            agent=agent
        )
    
    def report_writing(self, agent):
        return Task(
            description=f"""Review and synthesize all the findings from the News Research Expert, Stock Price Seeker and the Fillings Research Expert and use that to
            write a clear, explanatory report to guide your user's investment decision making. Make sure the current stock price of the company is 
            emphasized in your report.

            You do not need to do an analysis of the company's stock but you MUST mention the current stock price which you got from the Stok Price Seeker.

            Your final answer must be a full detailed report capturing all the qantitative and qualitative data provided
            and must be easy to read and understand as well.
            
            {self.__tip_section()}""",
            agent=agent
        )
    
    def __tip_section(self):
        return "If you do your BEST job, I'll tip you $500."
