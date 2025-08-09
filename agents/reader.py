import os
import requests
from groq import Groq
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from requests.auth import HTTPBasicAuth
from agents.test_case_formatter import TestCaseFormatter

load_dotenv()



# --- Groq Client ---
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# --- Confluence Fetcher ---
def get_confluence_text(page_id):
    token = os.getenv("CONFLUENCE_API_TOKEN")
    base_url = os.getenv("CONFLUENCE_BASE_URL")
    url = f"{base_url}/rest/api/content/{page_id}?expand=body.storage"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    html_content = res.json()["body"]["storage"]["value"]
    return BeautifulSoup(html_content, "html.parser").get_text(separator="\n")

# --- Jira Fetcher ---
def get_jira_ticket(ticket_key):
    email = os.getenv("JIRA_EMAIL")
    token = os.getenv("JIRA_API_TOKEN")
    base_url = os.getenv("JIRA_BASE_URL")
    url = f"{base_url}/rest/api/3/issue/{ticket_key}"
    auth = HTTPBasicAuth(email, token)
    headers = {"Accept": "application/json"}
    res = requests.get(url, headers=headers, auth=auth)
    res.raise_for_status()
    data = res.json()
    summary = data["fields"]["summary"]
    description = data["fields"]["description"]
    desc_text = "No description."
    if description:
        for block in description.get("content", []):
            for inner in block.get("content", []):
                if inner.get("type") == "text":
                    desc_text += inner["text"] + "\n"
    return f"Summary: {summary}\nDescription: {desc_text}"

# --- QA Test Agent ---
def qa_test_agent(source_type, source_id):
    if source_type == "confluence":
        content = get_confluence_text(source_id)
    elif source_type == "jira":
        content = get_jira_ticket(source_id)
    else:
        raise ValueError("Invalid source_type")

    prompt = f"""
    You are a senior QA automation engineer.
    Based on the following context, generate detailed, testable steps with expected results:

    {content}
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a helpful QA test case generator."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    # Example: Confluence
    #print(qa_test_agent("confluence", "131247"))
    
    #Example: Jira
   formatter = TestCaseFormatter(qa_test_agent("jira", "CP-1"))
   structured_cases = formatter.to_csv_list()
   print("Structured Test Cases:", structured_cases)
