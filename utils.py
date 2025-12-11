import openai
from fpdf import FPDF
from fpdf.errors import FPDFUnicodeEncodingException
from fpdf.enums import XPos, YPos
import io
import re
from tavily import TavilyClient
from exa_py import Exa

REACT_SYSTEM_PROMPT = """
Answer the following question. You have access to the following tools:

search_discovery: Call this tool to perform a broad web search or find industry landscape information. Use this for "Discovery". Input: a search query.
search_fact: Call this tool to verify specific facts, numbers, or retrieve targeted information. Use this for "Fact Retrieval". Input: a search query.

Use the following format:

Question: the input question
Thought: you should always think about what to do
Action: the action to take, should be one of [search_discovery, search_fact]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!
"""

def tavily_search(query, api_key):
    """
    Performs a targeted search using Tavily.
    """
    try:
        client = TavilyClient(api_key=api_key)
        response = client.search(query, search_depth="basic")
        context = [f"Source: {res['url']}\nContent: {res['content']}" for res in response.get('results', [])]
        return "\n\n".join(context)
    except Exception as e:
        return f"Error performing Tavily search: {str(e)}"

def exa_search(query, api_key):
    """
    Performs a semantic search using Exa (formerly Metaphor).
    """
    try:
        exa = Exa(api_key=api_key)
        # We use search_and_contents to get snippets directly
        response = exa.search_and_contents(
            query,
            num_results=3,
            use_autoprompt=True,
            text=True
        )
        context = [f"Title: {res.title}\nSource: {res.url}\nContent: {res.text[:500]}..." for res in response.results]
        return "\n\n".join(context)
    except Exception as e:
        return f"Error performing Exa search: {str(e)}"

def stream_deep_research(api_key, messages, tavily_api_key=None, exa_api_key=None):
    """
    Streams the response from the Deep Research model via OpenRouter.
    Implements a ReAct loop if tools (Tavily or Exa) are provided.
    """
    client = openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    internal_messages = list(messages)

    # Inject System Prompt if any tool is enabled
    if tavily_api_key or exa_api_key:
        system_msg_exists = False
        for msg in internal_messages:
            if msg['role'] == 'system':
                if "Answer the following question. You have access to the following tools" not in msg['content']:
                     msg['content'] += f"\n\n{REACT_SYSTEM_PROMPT}"
                system_msg_exists = True
                break

        if not system_msg_exists:
            internal_messages.insert(0, {"role": "system", "content": REACT_SYSTEM_PROMPT})

    MAX_STEPS = 5
    step_count = 0

    while step_count < MAX_STEPS:
        step_count += 1

        try:
            stream = client.chat.completions.create(
                model="alibaba/tongyi-deepresearch-30b-a3b:free",
                messages=internal_messages,
                stream=True
            )

            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield content

            if not tavily_api_key and not exa_api_key:
                break

            # Parse for Action
            # Regex to match Action: [action_name] and Action Input: [input]
            # Supported actions: search_discovery, search_fact
            action_match = re.search(r"Action:\s*(search_discovery|search_fact)", full_response, re.IGNORECASE)
            input_match = re.search(r"Action Input:\s*(.+)", full_response, re.IGNORECASE)

            if action_match and input_match:
                action_name = action_match.group(1).lower()
                tool_input = input_match.group(1).strip()
                # Remove any trailing "Observation:" if the model hallucinated it
                tool_input = tool_input.split("Observation:")[0].strip()

                observation = ""

                if action_name == "search_discovery":
                    if exa_api_key:
                        yield f"\n\n*Executing Discovery Search (Exa): {tool_input}*\n\n"
                        observation = exa_search(tool_input, exa_api_key)
                    else:
                        observation = "Error: Exa API Key not provided. Cannot perform Discovery Search."
                        yield f"\n\n*{observation}*\n\n"

                elif action_name == "search_fact":
                    if tavily_api_key:
                        yield f"\n\n*Executing Fact Search (Tavily): {tool_input}*\n\n"
                        observation = tavily_search(tool_input, tavily_api_key)
                    else:
                        observation = "Error: Tavily API Key not provided. Cannot perform Fact Search."
                        yield f"\n\n*{observation}*\n\n"

                # Update history
                internal_messages.append({"role": "assistant", "content": full_response})
                internal_messages.append({"role": "user", "content": f"Observation: {observation}"})

                yield f"\n\n*Observation obtained. Analyzing...*\n\n"

                # Loop continues
            else:
                # No action found, we are done
                break

        except Exception as e:
            yield f"Error: {str(e)}"
            break

def generate_pdf(text):
    """
    Generates a PDF from the provided text and returns the bytes.
    Uses fpdf2.
    """
    class PDF(FPDF):
        def header(self):
            # Attempt to use DejaVuSans if registered, else fallback
            font_family = 'DejaVu' if 'DejaVu' in self.fonts else 'helvetica'
            self.set_font(font_family, 'B', 12)
            self.cell(0, 10, 'Deep Research Report', border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
            self.ln(10)

        def footer(self):
            self.set_y(-15)
            font_family = 'DejaVu' if 'DejaVu' in self.fonts else 'helvetica'
            self.set_font(font_family, 'I', 8)
            self.cell(0, 10, f'Page {self.page_no()}', border=0, new_x=XPos.RIGHT, new_y=YPos.TOP, align='C')

    pdf = PDF()

    # Register the Unicode font
    try:
        pdf.add_font('DejaVu', '', 'assets/fonts/DejaVuSans.ttf')
        pdf.add_font('DejaVu', 'B', 'assets/fonts/DejaVuSans.ttf') # Using regular for bold for now if bold not available
        pdf.add_font('DejaVu', 'I', 'assets/fonts/DejaVuSans.ttf') # Using regular for italic for now if italic not available
        font_family = 'DejaVu'
    except Exception:
        font_family = 'helvetica'

    pdf.add_page()
    pdf.set_font(font_family, size=12)

    try:
        # Try to use markdown=True if available in this version of fpdf2
        # Use a compatible font if loaded
        pdf.multi_cell(0, 10, text, markdown=True)
    except TypeError:
        # Fallback for older versions or if markdown param is not supported in this specific way
        pdf.multi_cell(0, 10, text)
    except (UnicodeEncodeError, FPDFUnicodeEncodingException):
        # Fallback for fpdf2 if it tries to encode and fails (should be rare with DejaVu)
        # We manually sanitize if the automatic handling fails
        sanitized_text = text.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 10, sanitized_text)

    # fpdf2 output() returns a bytearray if no name is provided
    return bytes(pdf.output())
