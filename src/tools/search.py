import asyncio
from langchain_core.tools import tool
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from src.logger import get_logger

logger = get_logger(__name__)

@tool(parse_docstring=True)
async def duck_duck_go_search(query: str, max_results: int = 5) -> str:
    """Execute a DuckDuckGo web search and return formatted results.

    Performs a live web search using the DuckDuckGoSearchAPIWrapper and
    formats the top search results into a readable string. Intended for
    gathering recent news, competitor updates, and market analysis.

    Args:
        query (str): The search query string (e.g., "Apple AI hardware strategy 2026").
        max_results (int, optional): Maximum number of results to return. Defaults to 5.
    """
    try:
        logger.info(f"Executing web search for: '{query}'")
        search_wrapper = DuckDuckGoSearchAPIWrapper(max_results=max_results)

        search_results = await asyncio.to_thread(
            search_wrapper.results, query, max_results
        )

        if not search_results:
            logger.warning(f"No results found for query: {query}")
            return f"No results found for query: {query}"

        formatted_results = f"--- WEB SEARCH RESULTS FOR: '{query}' ---\n"
        for idx, result in enumerate(search_results, 1):
            formatted_results += f"[{idx}] Title: {result.get('title')}\n"
            formatted_results += f"    Source: {result.get('link')}\n"
            formatted_results += f"    Snippet: {result.get('snippet')}\n\n"
        formatted_results += "----------------------------------------"

        logger.debug(f"Search successful for query: '{query}'")
        return formatted_results
    except Exception as e:
        logger.error(f"Error executing search for '{query}': {str(e)}")
        return f"Error executing search for '{query}': {str(e)}"