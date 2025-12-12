import openai
import logging
from fpdf import FPDF
from fpdf.errors import FPDFUnicodeEncodingException
from fpdf.enums import XPos, YPos
import re
import json
import os
from datetime import datetime
from tavily import TavilyClient
from exa_py import Exa

# Configure logging
logging.basicConfig(
    filename='deep_research.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rate Limits
USAGE_FILE = "usage.json"
DAILY_LIMIT = 30
MONTHLY_LIMIT = 1000

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

def check_and_update_limit(service_name):
    """
    Checks if the rate limit for the given service has been reached.
    Updates the usage count if within limits.
    Returns (True, "") if allowed, or (False, reason) if blocked.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    this_month = datetime.now().strftime("%Y-%m")

    initial_service_data = {"day": today, "month": this_month, "daily_count": 0, "monthly_count": 0}

    # Initialize usage data if file doesn't exist or is invalid
    usage_data = {}
    if os.path.exists(USAGE_FILE):
        try:
            with open(USAGE_FILE, "r") as f:
                usage_data = json.load(f)
        except json.JSONDecodeError:
            pass # usage_data remains empty, will be populated below

    # Ensure services exist in data
    if "tavily" not in usage_data:
        usage_data["tavily"] = initial_service_data.copy()
    if "exa" not in usage_data:
        usage_data["exa"] = initial_service_data.copy()

    service_data = usage_data.get(service_name)
    if not service_data:
        # Fallback if service_name is new or unexpected
        service_data = initial_service_data.copy()
        usage_data[service_name] = service_data

    # Check for Month Reset
    if service_data["month"] != this_month:
        service_data["month"] = this_month
        service_data["monthly_count"] = 0
        service_data["day"] = today
        service_data["daily_count"] = 0 # New month implies new day

    # Check for Day Reset
    elif service_data["day"] != today:
        service_data["day"] = today
        service_data["daily_count"] = 0

    # Check Limits
    if service_data["monthly_count"] >= MONTHLY_LIMIT:
        return False, f"Monthly limit of {MONTHLY_LIMIT} requests reached for {service_name}. Resets on {this_month}-01 (next month)."

    if service_data["daily_count"] >= DAILY_LIMIT:
        return False, f"Daily limit of {DAILY_LIMIT} requests reached for {service_name}. Resets tomorrow."

    # Increment Usage
    service_data["daily_count"] += 1
    service_data["monthly_count"] += 1

    # Save back to file
    try:
        with open(USAGE_FILE, "w") as f:
            json.dump(usage_data, f, indent=4)
    except Exception as e:
        return False, f"Error saving usage data: {str(e)}"

    return True, ""

def tavily_search(query, api_key):
    """
    Performs a targeted search using Tavily.
    """
    # allowed, message = check_and_update_limit("tavily")
    # if not allowed:
    #     return f"Error: {message}"

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
    # allowed, message = check_and_update_limit("exa")
    # if not allowed:
    #     return f"Error: {message}"

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

def stream_deep_research(messages, api_keys):
    """
    Streams the response from the Deep Research model via OpenRouter.
    Implements a ReAct loop if tools (Tavily or Exa) are provided.
    """
    logger.info("Starting deep research stream")

    if not api_keys.get("openrouter"):
        logger.error("OpenRouter API Key not provided")
        yield "Error: OpenRouter API Key not provided."
        return

    # Log key details (masked) for debugging
    key = api_keys["openrouter"]
    masked_key = f"{key[:8]}...{key[-4:]}" if len(key) > 12 else "***"
    logger.info(f"Using OpenRouter Key: {masked_key} (Length: {len(key)})")

    client = openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_keys["openrouter"],
        default_headers={
            "HTTP-Referer": "http://localhost:8501",
            "X-Title": "Deep Research Agent",
        }
    )

    internal_messages = list(messages)

    # Determine available tools
    available_tools = []
    if api_keys.get("exa"):
        available_tools.append("search_discovery")
    if api_keys.get("tavily"):
        available_tools.append("search_fact")

    # Inject System Prompt if tools are available
    if available_tools:
        system_prompt = REACT_SYSTEM_PROMPT
        system_msg_exists = False
        for msg in internal_messages:
            if msg['role'] == 'system':
                if "Answer the following question. You have access to the following tools" not in msg['content']:
                        msg['content'] += f"\n\n{system_prompt}"
                system_msg_exists = True
                break

        if not system_msg_exists:
            internal_messages.insert(0, {"role": "system", "content": system_prompt})
    else:
        # If no tools, we don't inject ReAct prompt, just rely on model knowledge
        pass

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

            # Check if we should look for actions
            if not available_tools:
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

                if action_name == "search_discovery" and "search_discovery" in available_tools:
                    yield f"\n\n*Executing Discovery Search (Exa): {tool_input}*\n\n"
                    observation = exa_search(tool_input, api_keys["exa"])
                    if observation.startswith("Error:"):
                         yield f"\n\n*{observation}*\n\n"

                elif action_name == "search_fact" and "search_fact" in available_tools:
                    yield f"\n\n*Executing Fact Search (Tavily): {tool_input}*\n\n"
                    observation = tavily_search(tool_input, api_keys["tavily"])
                    if observation.startswith("Error:"):
                         yield f"\n\n*{observation}*\n\n"

                else:
                    # Model tried to use a tool it doesn't have access to or hallucinates
                    yield f"\n\n*Model attempted to use {action_name} but key is missing.*\n\n"
                    break

                # Update history
                internal_messages.append({"role": "assistant", "content": full_response})
                internal_messages.append({"role": "user", "content": f"Observation: {observation}"})

                yield f"\n\n*Observation obtained. Analyzing...*\n\n"

                # Loop continues
            else:
                # No action found, we are done
                break

        except Exception as e:
            logger.error(f"Error during streaming: {str(e)}", exc_info=True)
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
