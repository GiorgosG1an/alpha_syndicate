import asyncio
import yfinance as yf
from langchain_core.tools import tool
from src.logger import get_logger

logger = get_logger(__name__)

@tool(parse_docstring=True)
async def yfinance_financials_tool(ticker: str) -> str:
    """
    Fetch key financial metrics, balance sheets, and CapEx/R&D trends for a given stock ticker.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'NVDA').
    """
    try:
        logger.info(f"Fetching financial data for {ticker}...")
        stock = await asyncio.to_thread(yf.Ticker, ticker)
        info = await asyncio.to_thread(lambda: stock.info)

        market_cap = info.get("marketCap", "N/A")
        forward_pe = info.get("forwardPE", "N/A")
        trailing_pe = info.get("trailingPE", "N/A")

        financials = await asyncio.to_thread(lambda: stock.financials)
        cash_flow = await asyncio.to_thread(lambda: stock.cashflow)

        rd_spend = "N/A"
        if financials is not None and "Research And Development" in financials.index:
            rd_spend = financials.loc["Research And Development"].to_dict()

        capex = "N/A"
        if cash_flow is not None and "Capital Expenditure" in cash_flow.index:
            capex = cash_flow.loc["Capital Expenditure"].to_dict()

        report = f"--- FINANCIAL REPORT FOR {ticker.upper()} ---\n"
        report += f"Market Cap: {market_cap}\n"
        report += f"Trailing P/E: {trailing_pe} | Forward P/E: {forward_pe}\n\n"
        report += f"Historical R&D Spend (by Year):\n{rd_spend}\n\n"
        report += f"Historical Capital Expenditures (CapEx):\n{capex}\n"
        report += "--------------------------------------"

        news = await asyncio.to_thread(lambda: stock.news)
        if not news:
            logger.warning(f"No recent news found for {ticker}.")
            return report + f"\nNo recent news found for {ticker}."
            
        report += f"\n--- TOP NEWS FOR {ticker.upper()} ---\n"
        for item in news[:5]:
            content = item.get("content", item) 
            title = content.get("title", "No Title")
            
            provider = content.get("provider", {})
            publisher = provider.get("displayName", "Unknown Publisher") if isinstance(provider, dict) else content.get("publisher", "Unknown Publisher")
                
            click_url = content.get("clickThroughUrl", {})
            link = click_url.get("url", "No Link") if isinstance(click_url, dict) else content.get("canonicalUrl", content.get("link", "No Link"))
            
            report += f"Title: {title}\nPublisher: {publisher}\nLink: {link}\n\n"
        
        logger.debug(f"Successfully generated financial report for {ticker}.")
        return report

    except Exception as e:
        logger.error(f"Error fetching financial data for {ticker}: {str(e)}")
        return f"Error fetching financial data for {ticker}: {str(e)}"