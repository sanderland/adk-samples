from google.adk import Agent
from google.adk.tools import FunctionTool

from agent.tools.system_tools import *
from agent.tools.web_search import web_search

instructions = """
You are my friend. I love you. If asked about something you don't know, use a tool or call one of your sub agents.
You have access to the following tools:
- Get current time
- Get disk space
"""


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

agent = Agent(
    model="gemini-2.0-flash-001",
    name="super_agent",
    instruction=instructions,
    sub_agents=[search_agent],
    tools=[
        FunctionTool(
            func=get_current_time,
        ),
        FunctionTool(
            func=get_disk_space,
        ),
        FunctionTool(
            func=get_system_info,
        )
    ],
)
