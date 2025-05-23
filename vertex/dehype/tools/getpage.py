import requests

def fetch_and_parse_webpage(url: str) -> str:
    """Fetches the content of a webpage and parses it using BeautifulSoup.


    Args:
      url (str): The URL of the webpage to fetch.
    Returns:
      str: The parsed text content of the webpage, or an error message if the fetch fails.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"
