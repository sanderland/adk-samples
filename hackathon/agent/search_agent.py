from google.adk import Agent
from google.adk.tools import FunctionTool

from agent.tools.web_search import web_search

search_agent_prompt = """
You can search the web using Tavily API. 
"""

search_agent = Agent(
    model="gemini-2.0-flash-001",
    name="search_agent",
    instruction=search_agent_prompt,
    sub_agents=[],
    tools=[
        FunctionTool(
            func=web_search,
        ),
    ],
)
