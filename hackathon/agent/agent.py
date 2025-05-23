from google.adk import Agent
from google.adk.tools import FunctionTool

from agent.tools.system_tools import *
from agent.search_agent import search_agent
from agent.fact_checker_agent import fact_checker_agent

instructions = """
You are my friend. I love you. If asked about something you don't know, use a tool or call one of your sub agents.

You have access to the following tools:
- Get current time
- Get disk space
- Get system info

You have specialized sub-agents:
- search_agent: For web searches
- fact_checker_agent: For fact-checking statements and analyzing PDF documents for veracity

When asked to:
- Verify the veracity of a PDF or analyze a PDF for credibility, transfer to fact_checker_agent
- Fact-check statements or claims, transfer to fact_checker_agent
- Search the web, transfer to search_agent

Note: For PDF analysis, provide a file path or publicly accessible URL to the fact_checker_agent.
If a user uploads a PDF directly, ask them to provide a file path or URL instead.
"""

agent = Agent(
    model="gemini-2.0-flash-001",
    name="super_agent",
    instruction=instructions,
    sub_agents=[search_agent, fact_checker_agent],
    tools=[
        FunctionTool(
            func=get_current_time,
        ),
        FunctionTool(
            func=get_disk_space,
        ),
        FunctionTool(
            func=get_system_info,
        ),
    ],
)
