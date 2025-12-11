import streamlit as st
import utils

# Page Configuration
st.set_page_config(
    page_title="Deep Research Agent",
    page_icon="🔍",
    layout="wide"
)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

if "simple_report_content" not in st.session_state:
    st.session_state.simple_report_content = ""

# Sidebar Configuration
with st.sidebar:
    st.header("Settings")

    mode = st.radio(
        "Select Interface Mode",
        ["Simple Report Generator", "Chat Interface"],
        captions=["One-off research task", "Conversational research"]
    )

    st.markdown("---")
    st.info("Using model: `alibaba/tongyi-deepresearch-30b-a3b:free`")

# Main Content Area
st.title("Deep Research Agent 🔍")

# Logic for different modes will go here
if mode == "Simple Report Generator":
    st.subheader("Simple Report Generator")

    prompt = st.text_area("Enter your research topic or question:", height=150)

    if st.button("Start Research", type="primary"):
        if not prompt or not prompt.strip():
            st.error("Please enter a valid prompt.")
        else:
            st.session_state.simple_report_content = ""
            report_placeholder = st.empty()
            full_response = ""

            with st.spinner("Researching..."):
                # Stream the response
                messages = [{"role": "user", "content": prompt.strip()}]
                # No keys passed, using hardcoded ones in utils
                for chunk in utils.stream_deep_research(messages):
                    if chunk.startswith("Error:"):
                        st.error(chunk)
                        full_response = ""
                        break
                    full_response += chunk
                    report_placeholder.markdown(full_response + "▌")

                if full_response:
                    report_placeholder.markdown(full_response)
                    st.session_state.simple_report_content = full_response
                    st.success("Research Complete!")

    # Show download button if content exists
    if st.session_state.simple_report_content:
        pdf_bytes = utils.generate_pdf(st.session_state.simple_report_content)
        st.download_button(
            label="📄 Download Report as PDF",
            data=pdf_bytes,
            file_name="deep_research_report.pdf",
            mime="application/pdf"
        )

elif mode == "Chat Interface":
    st.subheader("Chat Interface")

    # Display chat messages from history
    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            # Add download button for assistant messages
            if message["role"] == "assistant":
                col1, col2 = st.columns([0.85, 0.15]) # Push button to the right/small column
                with col2:
                    pdf_bytes = utils.generate_pdf(message["content"])
                    st.download_button(
                        label="Download PDF",
                        data=pdf_bytes,
                        file_name=f"research_report_{idx}.pdf",
                        mime="application/pdf",
                        key=f"download_{idx}"
                    )

    # Chat input
    if prompt := st.chat_input("Ask a question or request research..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""

            # Stream the response
            # No keys passed, using hardcoded ones in utils
            for chunk in utils.stream_deep_research(st.session_state.messages):
                    if chunk.startswith("Error:"):
                        st.error(chunk)
                        full_response = "Error occurred." # Keep it simple for history
                        break
                    full_response += chunk
                    message_placeholder.markdown(full_response + "▌")

            message_placeholder.markdown(full_response)

        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": full_response})

        # Rerun to show the download button for the new message immediately
        st.rerun()
