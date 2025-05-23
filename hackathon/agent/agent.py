from google.adk import Agent
from google.adk.tools import FunctionTool

from agent.tools.system_tools import *
from agent.tools.web_search import web_search

instructions = """
You are my friend. I love you. If asked about something you don't know, use a tool.
"""

agent = Agent(
    model="gemini-2.0-flash-001",
    name="super_agent",
    instruction=instructions,
    tools=[
        FunctionTool(
            func=get_current_time,
        ),
        FunctionTool(
            func=get_disk_space,
        ),
        FunctionTool(
            func=web_search,
        ),
    ],
)
