# Deep Research Agent 🔍

A powerful research assistant powered by the **Tongyi DeepResearch 30B** model. This Streamlit application enables users to perform deep, autonomous research tasks, generate comprehensive reports, and verify facts in real-time.

## 🚀 Features

-   **Dual Interface Modes**:
    -   **Simple Report Generator**: Generate a one-off, comprehensive research report on any topic.
    -   **Chat Interface**: Interact conversationally with the agent to refine queries and explore topics in depth.
-   **Autonomous Web Search**: The agent uses a ReAct (Reasoning and Acting) loop to autonomously gather information:
    -   **Discovery Search (Exa)**: Used for broad landscape analysis and finding relevant resources.
    -   **Fact Search (Tavily)**: Used for verifying specific numbers, dates, and facts.
-   **Real-time Streaming**: Watch the agent's thought process, tool executions, and report generation in real-time.
-   **PDF Export**: Download reports as cleanly formatted PDFs with Unicode support (via DejaVu Sans).
-   **Secure**: API keys are handled locally within the session and never stored.

## 🛠️ Technology Stack

-   **Frontend**: [Streamlit](https://streamlit.io/)
-   **LLM**: `alibaba/tongyi-deepresearch-30b-a3b:free` (via OpenRouter)
-   **Search Tools**:
    -   [Exa (formerly Metaphor)](https://exa.ai/)
    -   [Tavily](https://tavily.com/)
-   **PDF Generation**: `fpdf2`

## 📋 Prerequisites

To use the full capabilities of the agent, you will need:
1.  **OpenRouter API Key** (Required): To access the LLM.
2.  **Tavily API Key** (Optional): For fact-checking and specific queries.
3.  **Exa API Key** (Optional): For broad discovery and context gathering.

## 📦 Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd deep-research-agent
    ```

2.  **Create and activate a virtual environment** (Recommended):
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## 🎮 Usage

1.  **Run the application**:
    ```bash
    streamlit run app.py
    ```

2.  **Configure the Agent**:
    -   Open the sidebar on the left.
    -   Enter your **OpenRouter API Key**.
    -   (Optional) Enter **Tavily** and **Exa** keys to enable web search capabilities.
    -   *Note: Without search keys, the agent will rely solely on its internal knowledge base.*

3.  **Select a Mode**:
    -   **Simple Report Generator**: Enter a topic (e.g., "The future of solid-state batteries") and click "Start Research".
    -   **Chat Interface**: Chat naturally (e.g., "Find me the latest papers on transformers" followed by "Summarize the third one").

4.  **Export Results**:
    -   Click the "Download PDF" button to save the generated content.

## 🧠 How it Works

The agent utilizes a **ReAct** loop, allowing it to "think" before it "acts".
1.  **Thought**: The model analyzes the user's request and determines if it needs external information.
2.  **Action**: If needed, it calls the `search_discovery` (Exa) or `search_fact` (Tavily) tools.
3.  **Observation**: The search results are fed back into the model's context.
4.  **Answer**: The model synthesizes the information to generate the final response or report.

*The agent is configured to perform up to 5 steps of reasoning/searching per request to ensure timely responses.*

## ❓ Troubleshooting

-   **Garbled Text in PDF**: Ensure `assets/fonts/DejaVuSans.ttf` exists. The system falls back to Helvetica if the font is missing, which may not support all Unicode characters.
-   **"Error: ... API Key not provided"**: The agent attempted to use a tool but the key was missing. Provide the key in the sidebar or ask a question that doesn't require live data.
-   **Model Errors**: If you receive errors from OpenRouter, check your credit balance or network connection.
