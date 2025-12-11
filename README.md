# Deep Research Agent

A powerful Streamlit application designed to perform deep research using the **Tongyi DeepResearch 30B A3B** model via OpenRouter. This tool offers real-time streaming of research results and the ability to export findings as professional PDF reports.

## Features

-   **Dual Interface Modes**:
    -   **Simple Report Generator**: Ideal for one-off research tasks. Enter a topic, get a comprehensive report.
    -   **Chat Interface**: Engage in a conversational research session to refine queries and explore topics in depth.
-   **Real-time Streaming**: Watch the research report being generated token by token.
-   **PDF Export**: Download your research findings as a clean, formatted PDF document.
-   **Secure Configuration**: API keys are handled securely within the session.

## Prerequisites

-   Python 3.8 or higher
-   An [OpenRouter](https://openrouter.ai/) API Key

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
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

3.  **Start Researching:**
    -   Select your preferred mode: **Simple Report Generator** or **Chat Interface**.
    -   Enter your research topic or question.
    -   Wait for the model to generate the insights.
    -   Download the result as a PDF if desired.

## Technology Stack

-   **Frontend**: [Streamlit](https://streamlit.io/)
-   **Model**: `alibaba/tongyi-deepresearch-30b-a3b:free` (via OpenRouter)
-   **PDF Generation**: `fpdf2`
-   **API Client**: `openai` (Python client)
