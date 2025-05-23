from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool,google_search

from . import prompt
from .tools import fetch_and_parse_webpage, extract_pdf_text


MODEL = "gemini-2.5-pro-preview-05-06"
MODEL = "gemini-2.5-flash-preview-05-20"



source_finder = LlmAgent(
    name="dehype",
    model=MODEL,
    description=(
        "Finding the original reliable source of information, "
        "and summarizing the information, both the hyped and the original"
    ),
    instruction=prompt.DEHYPE_PROMPT,
    output_key="dehyped_summary",
    tools=[google_search,
        FunctionTool(fetch_and_parse_webpage),
        FunctionTool(extract_pdf_text),
    ],
)

root_agent = source_finder
