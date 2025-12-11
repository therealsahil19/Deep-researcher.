import openai
from fpdf import FPDF
from fpdf.errors import FPDFUnicodeEncodingException
from fpdf.enums import XPos, YPos
import io
import re
from tavily import TavilyClient

REACT_SYSTEM_PROMPT = """
Answer the following question. You have access to the following tools:

search: Call this tool to search the web. Input: a search query.

Use the following format:

Question: the input question
Thought: you should always think about what to do
Action: the action to take, should be one of [search]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!
"""

def tavily_search(query, api_key):
    try:
        client = TavilyClient(api_key=api_key)
        response = client.search(query, search_depth="basic")
        context = [f"Source: {res['url']}\nContent: {res['content']}" for res in response.get('results', [])]
        return "\n\n".join(context)
    except Exception as e:
        return f"Error performing search: {str(e)}"

def stream_deep_research(api_key, messages, tavily_api_key=None):
    """
    Streams the response from the Deep Research model via OpenRouter.
    Implements a ReAct loop if tavily_api_key is provided.
    """
    client = openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    internal_messages = list(messages)

    # Inject System Prompt if Tavily is enabled
    if tavily_api_key:
        system_msg_exists = False
        for msg in internal_messages:
            if msg['role'] == 'system':
                # Avoid duplicating the prompt if it's already there (e.g. from previous turns if we were persisting internal_messages, which we aren't here, but good practice)
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

            if not tavily_api_key:
                break

            # Parse for Action
            # Look for the last occurrence of Action: and Action Input:
            action_match = re.search(r"Action:\s*(search)", full_response, re.IGNORECASE)
            input_match = re.search(r"Action Input:\s*(.+)", full_response, re.IGNORECASE)

            # Also check if "Final Answer" is present. If so, we might stop,
            # BUT sometimes models hallucinate a final answer and then an action.
            # Ideally, if "Action" is present, we execute it.

            if action_match and input_match:
                # Basic check to ensure we haven't already reached a "Final Answer" before the Action
                # (Simple logic: if "Final Answer" index < "Action" index, maybe ignore?
                # But ReAct usually ends with Final Answer. If Action appears, it's usually before.)

                tool_input = input_match.group(1).strip()
                # Remove any trailing "Observation:" if the model hallucinated it
                tool_input = tool_input.split("Observation:")[0].strip()

                yield f"\n\n*Executing Search: {tool_input}*\n\n"

                observation = tavily_search(tool_input, tavily_api_key)

                # Update history
                internal_messages.append({"role": "assistant", "content": full_response})
                internal_messages.append({"role": "user", "content": f"Observation: {observation}"})

                yield f"\n\n*Observation obtained. Analyzing...*\n\n"

                # Loop continues to feed observation back to LLM
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
