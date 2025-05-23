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
from dehype.tools import fetch_and_parse_webpage, extract_pdf_text, read_pdf_fh
import sys, time
import streamlit as st
from io import BytesIO
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
    "description": """Summarize final information for the user. 
ONLY use when finished, and only by itself. 
DO NOT USE THIS TOOL UNTIL A REPUTABLE PRIMARY SOURCE IS FOUND.
MUST contain these sections as 'heading':
- Claim: The claim being analyzed.
- Judgement: A brief statement of the claim's veracity.
- Summary: a summary of the findings, both popular and academic.
- Sources: list of primary academic sources as title with link. Should not overlap with popular coverage. Should not be generic like 'various' or 'wikipedia'.",
""",
    "parameters": {
        "type": "object",
        "properties": {
            "sections": {
                "type": "array",
                "description": "A list of summary sections, each with a heading and text.",
                "items": {
                    "type": "object",
                    "properties": {
                        "heading": {
                            "type": "string",
                            "description": "The heading for this section."
                        },
                        "text": {
                            "type": "string",
                            "description": "The text content for this section."
                        }
                    },
                    "required": ["heading", "text"]
                }
            }
        },
        "required": ["sections"],
    },
}

def run_streamlit():
    st.set_page_config(page_title="DeHype: True Source Discovery", page_icon="🕵️‍♂️", layout="wide")
    st.title("🕵️‍♂️ DeHype: True Source Discovery")
    st.markdown("""
    <style>
    .big-font { font-size: 1.3em; }
    .stTextInput>div>div>input { font-size: 1.1em; }
    .stButton>button { font-size: 1.1em; }
    </style>
    """, unsafe_allow_html=True)
    st.markdown(
        """
        <div class="big-font">
        <b>DeHype</b> helps you trace any claim, article, or social post back to its original source and assess credibility.<br>
        <i>Paste a claim, URL, or upload a PDF to begin.</i>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Model selection dropdown
    model_options = [
        "gemini-2.5-flash-preview-05-20",
        "gemini-2.5-pro-preview-05-06"
    ]
    selected_model = st.selectbox("Select Gemini model", model_options, index=0)

    query = st.text_input("Enter a claim, URL, or question:", "my uncle says windmills are bad for the environment")
    pdf_file = st.file_uploader("Or upload a PDF", type=["pdf"])
    run_button = st.button("🔎 Analyze", type="primary")

    if run_button:
        with st.spinner("Analyzing with DeHype agent..."):
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
            # Use the selected model
            chat = client.chats.create(model=selected_model, config=generate_content_config)

            # If PDF uploaded, extract text
            if pdf_file is not None:
                extracted_pdf = read_pdf_fh(BytesIO(pdf_file.getvalue()))
                user_query = extracted_pdf['text']
                st.info(f"Extracted text from PDF: {len(str(user_query))} chars. Running DeHype on extracted content...")
                if user_query is None:
                    st.error(f"Failed to extract text from PDF: {extracted_pdf}. Please try another file.")
                    st.stop()
            else:
                user_query = query

            st.markdown("---")
            # Ensure user_query is a string before slicing
            if isinstance(user_query, str):
                st.markdown(f"**Initial Query:** {user_query[:500]}")
            else:
                st.markdown("**Initial Query:** [No valid text extracted]")
            response = chat.send_message(user_query)
            visited_urls = set()
            while True:
                tool_results = []
                function_calls = response.function_calls or []
                if not function_calls:
                    st.success("Analysis complete!")
                    st.markdown(f"### DeHype Report\n{response.text}")
                    break
                print(f"Got response with {len(function_calls)} function calls: {[fn.name for fn in function_calls]}")
                for fn in function_calls:
                    args = ", ".join(f"{key}={val}" for key, val in fn.args.items())
                    if fn.name == "summarize":
                       headings = {section['heading'] for section in fn.args['sections']}
                       print(fn)
                       if headings != {"Claim", "Judgement", "Summary", "Sources"}:
                           tool_result = f"Invalid summary sections: {headings}. Expected: {{'Claim', 'Judgement', 'Summary', 'Sources'}}"
                           tool_results.append((fn.name, args, tool_result))
                           print("Invalid summary sections {headings}. Skipping...")
                           continue
                       summary = "\n\n".join(f"## {section['heading']}\n\n{section['text']}" for section in  fn.args['sections'])
                       st.markdown(f"# Summary\n\n{summary}")
                       continue

                    with st.expander(f"{fn.name}({args})", expanded=False):
                        if fn.name == "search_web":
                            st.info(f"Searching: {fn.args['query']}")
                            t0 = time.time()
                            result = search_and_summarize_web(client, selected_model, fn.args["query"])
                            tool_result = str(result)
                            st.success(f"[{time.time()-t0:.1f}s] Search result: {getattr(result, 'text', str(result))}")
                        elif fn.name == "read_pdf":
                            st.info(f"Reading PDF: {fn.args['url']}")
                            tool_result = extract_pdf_text(fn.args["url"])
                            st.success(f"PDF result: read {len(str(tool_result))//1000:,d} KB")
                        elif fn.name == "read_web_page":
                            st.info(f"Reading web page: {fn.args['url']}")
                            if fn.args["url"] in visited_urls:
                                tool_result = "Already visited this URL. Skipping."
                                print(f"{fn.args['url']}: Already visited this URL. Skipping.")
                            else:
                                tool_result = fetch_and_parse_webpage(fn.args["url"])
                                print(f"Read web page {fn.args['url']}: {len(tool_result)}")
                            st.success(f"Web page result: {len(str(tool_result))//1000:,d} KB")
                        else:
                            st.error(f"Unknown function: {fn.name}")
                            continue
                        if tool_result:
                            tool_results.append((fn.name, args, tool_result))
                if not tool_results:
                    print("No more tool calls. Done!")
                    break
                message = "Tool call results:\n"
                for name, args, result in tool_results:
                    message += f"{name}({args}): {str(result)[:2000]}\n\n"
                message += "Continue the task."
                print("--> Instructing model to continue...")
                response = chat.send_message(message)

if __name__ == "__main__":
    run_streamlit()
