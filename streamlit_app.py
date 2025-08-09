import os
import io
import tempfile
import streamlit as st
from dotenv import load_dotenv
from agents.reader import qa_test_agent
from agents.test_case_formatter import TestCaseFormatter

load_dotenv()

st.set_page_config(page_title="Autonomous QA Test Agent", layout="wide")

st.title("🤖 Autonomous QA Test Agent")
st.markdown("Generate, format, and export test cases from Confluence or Jira using Groq AI.")

source_type = st.selectbox("Source Type", ["jira", "confluence"])
source_id = st.text_input(
    "Source ID (JIRA Ticket Key or Confluence)",
    value="",  # default value
    placeholder="e.g., CP-1(Login to Banking App) or CP-2(Account Summary) or CP-3(Withdrawal)"  # placeholder text
)


if st.button("Generate Test Cases"):
    if not source_type or not source_id:
        st.error("⚠ Please fill all the fields.")
    else:
        with st.spinner("Fetching and generating test cases..."):
            try:
                # Step 1: Fetch + Generate
                test_cases_text = qa_test_agent(source_type, source_id)

                # Step 2: Format
                formatter = TestCaseFormatter(qa_test_agent("jira", source_id))
                test_cases_json = formatter.to_json()

                # Step 3: Save to CSV
                csv_path = tempfile.NamedTemporaryFile(delete=False, suffix=".csv").name
                formatter.to_csv(csv_path)

                # Step 4: Show preview
                st.success("✅ Test cases generated successfully!")
                st.subheader("Preview (JSON)")
                st.json(test_cases_json)

                # Step 5: Download button
                with open(csv_path, "rb") as f:
                    st.download_button(
                        label="📄 Download Test Cases (CSV)",
                        data=f,
                        file_name="generated_test_cases.csv",
                        mime="text/csv"
                    )

            except Exception as e:
                st.error(f"❌ Error: {e}")
