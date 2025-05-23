import os
from tavily import TavilyClient


def web_search(query: str, max_results: int = 5) -> str:
    """
    Search the web using Tavily API.
    
    Args:
        query: The search query
        max_results: Maximum number of results to return (default: 5)
    
    Returns:
        A formatted string containing search results
    """
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return "Error: TAVILY_API_KEY environment variable not set"
    
    client = TavilyClient(api_key=api_key)
    
    try:
        response = client.search(query, max_results=max_results)
        
        # Format results
        results = []
        for i, result in enumerate(response.get('results', []), 1):
            results.append(f"{i}. {result['title']}\n   URL: {result['url']}\n   {result['content']}\n")
        
        return "\n".join(results) if results else "No results found"
    
    except Exception as e:
        return f"Error performing search: {str(e)}"