import re
import time
from playwright.sync_api import Page, expect

def test_deep_research_loop(page: Page):
    # 1. Open the app
    page.goto("http://localhost:8501")

    # Wait for the app to load
    page.wait_for_selector("text=Deep Research Agent")

    # 2. Ensure "Simple Report Generator" is selected (it's the default, but verify existence)
    # The radio button might be hidden or styled, so we look for the label
    expect(page.get_by_text("Simple Report Generator").first).to_be_visible()

    # 3. Enter the prompt
    prompt_text = "create a report to show all LLMs released in November 2025, along with their capabilities."
    # Streamlit text_area often has a label
    text_area = page.get_by_label("Enter your research topic or question:")
    text_area.fill(prompt_text)

    # 4. Click Start Research
    page.get_by_role("button", name="Start Research").click()

    # 5. Monitor the Output for ReAct Loop
    # We expect to see "Executing Discovery Search" or "Executing Fact Search"
    # and "Observation obtained".
    # Since it streams, we might need to wait a bit.

    # We'll poll the text content of the report area.
    # The report appears in a markdown container.

    found_action = False
    found_observation = False
    found_completion = False

    # Increase timeout for research (it can take time)
    start_time = time.time()
    timeout = 180 # 3 minutes max

    while time.time() - start_time < timeout:
        content = page.content()

        if "Executing Discovery Search" in content or "Executing Fact Search" in content:
            found_action = True
            print("Verified: Action (Search) executed.")

        if "Observation obtained" in content:
            found_observation = True
            print("Verified: Observation received.")

        if "Research Complete!" in content:
            found_completion = True
            print("Verified: Research Complete.")
            break

        time.sleep(1)

    assert found_completion, "Research did not complete within timeout."

    # If the LLM already knew the answer without searching, found_action might be false.
    # But for "November 2025" (future/present relative to training data usually), it SHOULD search.
    # Given the prompt, we expect a search.
    assert found_action, "The agent should have executed a search action (Discovery/Fact)."
    assert found_observation, "The agent should have received an observation from the tool."

    # 6. Verify Content
    # Check for some content in the output.
    # Since it's a generated report, exact text is hard, but it shouldn't be empty.
    # We can check if "November 2025" is in the output (reiteration of prompt) or "LLM".
    expect(page.get_by_text("Research Complete!")).to_be_visible()

    # 7. PDF Verification
    # Setup download listener
    with page.expect_download() as download_info:
        page.get_by_role("button", name="Download Report as PDF").click()

    download = download_info.value
    path = download.path()
    print(f"Downloaded file to: {path}")

    # Verify file size
    import os
    size = os.path.getsize(path)
    print(f"File size: {size} bytes")
    assert size > 1000, "PDF file is suspiciously small."

    # Verify it starts with PDF signature
    with open(path, "rb") as f:
        header = f.read(5)
        assert header == b"%PDF-", "File is not a valid PDF."

    print("Test Passed: Deep Research Agent works as expected.")
