# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Academic_websearch_agent for finding research papers using search tools."""

from google.adk import Agent
from google.adk.tools import google_search

from . import prompt

MODEL = "gemini-2.5-pro-preview-05-06"
MODEL = "gemini-2.0-flash-001"  

source_search_agent = Agent(
    model=MODEL,
    name="source_search_agent",
    description="Take a high level claim and find the most relevant sources to support and/or refute it.",
    instruction=prompt.GENERAL_SOURCE_SEARCH_PROMPT,
    output_key="relevant_sources",
    tools=[google_search],
)
