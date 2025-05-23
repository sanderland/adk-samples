


from google import genai
from google.genai import types


SEARCH_SYSTEM_INSTRUCTION = (
    "You are a helpful assistant that can search the web for information, focussed on tracking down a reliable source."
    "You will be provided with a query, and you should return the most relevant results."
    "Summarize the information a list of sources, with:"
    "- url"
    "- title"
    "- short summary of the content."
    "- sources cited, url and reason for citation."
)

def search_and_summarize_web(client, model, query):
    response = client.models.generate_content(
        model=model,
        contents=query,
        config=types.GenerateContentConfig(
            system_instruction=SEARCH_SYSTEM_INSTRUCTION,
            tools=[types.Tool(
                google_search=types.GoogleSearchRetrieval()
            )]
        )
    )
    return response