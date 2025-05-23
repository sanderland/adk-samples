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

"""Credibility_assessor_agent for assessing the credibility of information."""

from google.adk import Agent
from google.adk.tools import google_search # Import google_search

from . import prompt # This will refer to the prompt file in the same directory

MODEL = "gemini-2.5-pro-preview-05-06" # Or your preferred model

credibility_assessor_agent = Agent(
    model=MODEL,
    name="credibility_assessor_agent", # New name
    instruction=prompt.CREDIBILITY_ASSESSOR_PROMPT, # Will be defined in this directory's prompt.py
    tools=[google_search], # Added google_search tool
    output_key="credibility_assessment_results" # Added output key
)
