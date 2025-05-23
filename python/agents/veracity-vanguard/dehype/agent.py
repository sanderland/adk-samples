from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

from . import prompt
from .sub_agents.credibility_assessor.agent import credibility_assessor_agent # Import new agent
from .sub_agents.source_search import source_search_agent 

MODEL = "gemini-2.5-pro-preview-05-06"


source_finder = LlmAgent(
    name="dehype",
    model=MODEL,
    description=(
        "Finding the original reliable source of information, "
        "and summarizing the information, both the hyped and the original"
    ),
    instruction=prompt.DEHYPE_PROMPT,
    output_key="dehyped_summary",
    tools=[
        AgentTool(agent=source_search_agent),
#        AgentTool(agent=academic_websearch_agent),
#        AgentTool(agent=credibility_assessor_agent), # Use new agent
    ],
)

root_agent = source_finder
