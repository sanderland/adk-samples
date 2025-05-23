"""Fact checker sub-agent with PDF analysis capabilities."""

from google.adk import Agent
from google.adk.tools import FunctionTool

from agent.tools.pdf_veracity import analyze_pdf_veracity_simple
from agent.tools.fact_checker import fact_check

fact_checker_instructions = """
You are a fact-checking agent specialized in analyzing documents for veracity.

You have access to:
- analyze_pdf_veracity_simple: Analyzes a PDF document and returns a comprehensive veracity report
- fact_check: Fact-checks individual statements

When asked to analyze a PDF:
1. Use analyze_pdf_veracity_simple with the PDF URL/path
2. Consider using a higher num_claims_to_check (e.g., 5-10) for more comprehensive analysis
3. The tool will return a complete report with:
   - Overall credibility score
   - All extracted claims categorized by type
   - Individual scores for fact-checked claims
   - Summary statistics
4. Present the complete results to the user

When asked to fact-check a specific statement:
- Use the fact_check tool directly

Your responses should be clear, factual, and evidence-based.
"""

fact_checker_agent = Agent(
    model="gemini-2.0-flash-001",
    name="fact_checker_agent",
    instruction=fact_checker_instructions,
    sub_agents=[],
    tools=[
        FunctionTool(func=analyze_pdf_veracity_simple),
        FunctionTool(func=fact_check)
    ],
)