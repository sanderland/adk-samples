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

"""Tool to fetch website content."""

import requests
from bs4 import BeautifulSoup
from google.adk.tools import Tool


class FetchWebsiteTextTool(Tool):
  """Tool to fetch the main textual content of a website."""

  name = "fetch_website_text"
  description = "Fetches the main textual content from a given URL."

  def _call(self, url: str) -> str:
    """Fetches the main textual content from a given URL.

    Args:
      url: The URL of the website to fetch.

    Returns:
      The main textual content of the website, or an error message if fetching
      or parsing fails.
    """
    try:
      response = requests.get(url, timeout=10)
      response.raise_for_status()  # Raise an exception for bad status codes

      # Check if the content is HTML
      if "text/html" not in response.headers.get("Content-Type", ""):
        return "Error: Content is not HTML."

      soup = BeautifulSoup(response.content, "html.parser")

      # Remove script and style elements
      for script_or_style in soup(["script", "style"]):
        script_or_style.decompose()

      # Get text
      text = soup.get_text()

      # Break into lines and remove leading/trailing space on each
      lines = (line.strip() for line in text.splitlines())
      # Break multi-headlines into a line each
      chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
      # Drop blank lines
      text = "\n".join(chunk for chunk in chunks if chunk)

      if not text:
        return "Error: No text content found."

      return text

    except requests.exceptions.RequestException as e:
      return f"Error fetching URL: {e}"
    except Exception as e:
      return f"Error parsing HTML: {e}"
