from google.adk.agents import LlmAgent
#from google.adk.tools import FunctionTool
from google.adk.tools.agent_tool import AgentTool
import requests
from bs4 import BeautifulSoup

from . import prompt
from .sub_agents.source_search import source_search_agent 

MODEL = "gemini-2.5-pro-preview-05-06"
#MODEL = "gemini-2.5-flash-preview-05-20"


def fetch_and_parse_webpage(url: str) -> dict:
    """Fetches the content of a webpage and parses it using BeautifulSoup.


    Args:
      url (str): The URL of the webpage to fetch.
    Returns:
      str: The parsed text content of the webpage, or an error message if the fetch fails.
    """    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        # Remove script and style elements
        for script_or_style in soup(['script', 'style']):
            script_or_style.decompose()
        text = ' '.join(soup.stripped_strings)
        return text
    except Exception as e:
        return f'Error: {str(e)}'


source_finder = LlmAgent(
    name="dehype",
    model=MODEL,
    description=(
        "Finding the original reliable source of information, "
        "and summarizing the information, both the hyped and the original"
    ),
    instruction=prompt.DEHYPE_PROMPT,
    output_key="dehyped_summary",
#    sub_agents=[source_search_agent],
    tools=[
#        FunctionTool(fetch_and_parse_webpage),
        AgentTool(agent=source_search_agent),
#        AgentTool(agent=credibility_assessor_agent), # Use new agent
    ],
)

root_agent = source_finder
