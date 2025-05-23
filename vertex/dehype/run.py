from google import genai
from google.genai.types import (
    GenerateContentConfig,
    GoogleSearch,
    Tool,
    Part,
    Content,
    FunctionCallingConfig,
    ToolConfig,
)
from dehype.websearch_agent import search_and_summarize_web
from dehype.prompt import DEHYPE_PROMPT
from dehype.tools import fetch_and_parse_webpage, extract_pdf_text
import sys, time

MODEL = "gemini-2.5-flash-preview-05-20"


search_web = {
    "name": "search_web",
    "description": "Search the web for information.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to use on the web.",
            }
        },
        "required": ["query"],
    },
}

read_pdf = {
    "name": "read_pdf",
    "description": "Read and extract content from a PDF at a given URL.",
    "parameters": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL of the PDF to read.",
            }
        },
        "required": ["url"],
    },
}

read_web_page = {
    "name": "read_web_page",
    "description": "Read and extract content from a web page at a given URL.",
    "parameters": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL of the web page to read.",
            }
        },
        "required": ["url"],
    },
}

summarize = {
    "name": "summarize",
    "description": "Summarize final information for the user",
    "parameters": {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "The text to report to the user. This MUST contain these parts. # Claim: # Judgement: # Summary: # Primary source(s). DO NOT USE THIS TOOL UNTIL A PRIMARY SOURCE IS FOUND.",
            }
        },
        "required": ["text"],
    },
}


def generate():
    client = genai.Client(
        vertexai=True,
        project="qwiklabs-gcp-01-da509f78af23",
        location="global",
    )


    tools = [Tool(function_declarations=[read_pdf, read_web_page, search_web, summarize])]

    generate_content_config = GenerateContentConfig(
        temperature=0.75,
        top_p=0.95,
        max_output_tokens=4196,
        system_instruction=DEHYPE_PROMPT,
        tools=tools,
        tool_config=ToolConfig(
            function_calling_config=FunctionCallingConfig(
                mode="ANY", allowed_function_names=["search_web", "read_pdf", "read_web_page", "summarize"]
            )
        ),
    )

    chat = client.chats.create(model="gemini-2.0-flash", config=generate_content_config)

    query = ' '.join(sys.argv[1:]) or   "brunost cures cancer?"

    print(f"--> Sending initial query {query}")
    response = chat.send_message(query)
    while True:
        tool_results = []
        function_calls = response.function_calls or []
        print(f"Got response with {len(function_calls)} function calls")
        if not function_calls:
            print("--> No function calls, exiting.")
            print(f"Final response: {response.text}")
            break

        for fn in function_calls:
            args = ", ".join(f"{key}={val}" for key, val in fn.args.items())
            print(f"{fn.name}({args})")
            if fn.name == "summarize":
                print(f"Summary: {fn.args['text']}")
            elif fn.name == "search_web":
                print(f"Searching: {fn.args['query']}")
                t0 = time.time()                
                result = search_and_summarize_web(client, MODEL, fn.args["query"])
                tool_result = str(result)
                print(f"[{time.time()-t0:.1f}s] Search result: {result.text}")
            elif fn.name == "read_pdf":
                print(f"Reading PDF: {fn.args['url']}")
                tool_result = extract_pdf_text(fn.args["url"])
                print(f"PDF result: read {len(tool_result)} characters")
            elif fn.name == "read_web_page":
                print(f"Reading web page: {fn.args['url']}")
                tool_result = fetch_and_parse_webpage(fn.args["url"])
                print(f"Web page result: read {len(tool_result)} characters")
            else:
                raise ValueError(f"Unknown function: {fn.name}")
                
            if tool_result:
                tool_results.append((fn.name, args, tool_result))

        if not tool_results:
            print("--> Done!")
            break

        message = "Tool call results:\n"
        for name, args, result in tool_results:
            message += f"{name}({args}): {result}\n\n"

        message += "Continue the task."

        print("--> Instructing model to continue...")
        response = chat.send_message(message)

generate()
