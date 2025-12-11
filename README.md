# Deep Research Agent

A powerful Streamlit application designed to perform deep research using the **Tongyi DeepResearch 30B A3B** model via OpenRouter. This tool offers real-time streaming of research results, autonomous web searching capabilities, and the ability to export findings as professional PDF reports.

## Features

-   **Dual Interface Modes**:
    -   **Simple Report Generator**: Ideal for one-off research tasks. Enter a topic, get a comprehensive report.
    -   **Chat Interface**: Engage in a conversational research session to refine queries and explore topics in depth.
-   **Autonomous Web Search**: The agent can autonomously perform web searches to find real-time data using the Tavily API.
-   **Real-time Streaming**: Watch the research report being generated token by token, including the agent's thought process and search actions.
-   **PDF Export**: Download your research findings as a clean, formatted PDF document. Includes support for Unicode characters using DejaVu Sans font.
-   **Secure Configuration**: API keys are handled securely within the session.

## Prerequisites

-   Python 3.8 or higher
-   An [OpenRouter](https://openrouter.ai/) API Key
-   (Optional) A [Tavily](https://tavily.com/) API Key for real-time web search capabilities.

## Project Structure

-   `app.py`: The main entry point for the Streamlit application, handling the UI and state management.
-   `utils.py`: Contains utility functions for API interaction (`stream_deep_research`), Tavily search integration, and PDF generation (`generate_pdf`).
-   `assets/fonts/`: Directory containing fonts (specifically `DejaVuSans.ttf`) for proper Unicode support in PDFs.
-   `requirements.txt`: List of Python dependencies.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/deep-research-agent.git
    cd deep-research-agent
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Run the application:**
    ```bash
    streamlit run app.py
    ```

2.  **Configure the Agent:**
    -   Once the app launches in your browser, look for the sidebar on the left.
    -   Enter your **OpenRouter API Key**.
    -   (Optional) Enter your **Tavily API Key** to enable web searching.

3.  **Start Researching:**
    -   Select your preferred mode: **Simple Report Generator** or **Chat Interface**.
    -   Enter your research topic or question.
    -   Wait for the model to generate the insights. If Tavily is enabled, you may see the agent searching for information.
    -   Download the result as a PDF if desired.

## Troubleshooting

-   **PDF Character Issues**: If the PDF export shows garbled characters or missing symbols, ensure that `assets/fonts/DejaVuSans.ttf` is present in your project directory. The application relies on this font for Unicode support.
-   **API Errors**: If you encounter errors starting with "Error:", check your OpenRouter API key and internet connection. Ensure you have credits or access to the `alibaba/tongyi-deepresearch-30b-a3b:free` model.
-   **Search Not Working**: Ensure you have provided a valid Tavily API Key in the sidebar.

## Technology Stack

-   **Frontend**: [Streamlit](https://streamlit.io/)
-   **Model**: `alibaba/tongyi-deepresearch-30b-a3b:free` (via OpenRouter)
-   **Web Search**: [Tavily API](https://tavily.com/)
-   **PDF Generation**: `fpdf2`
-   **API Client**: `openai` (Python client)
