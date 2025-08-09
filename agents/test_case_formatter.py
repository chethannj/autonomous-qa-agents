import json
import re
import csv
import io
from typing import List, Dict, Union
from typing import List, Dict, Union
from openpyxl import Workbook

class TestCaseFormatter:
    """
    Formats raw LLM test case output into structured formats like JSON, CSV-friendly lists, or plain text.
    """

    def __init__(self, raw_text: str):
        self.raw_text = raw_text.strip()

    def to_json(self) -> List[Dict[str, Union[str, List[str]]]]:
        """
        Attempts to parse test cases into JSON format.
        Expected format from LLM: numbered or bullet-pointed test cases with steps and expected results.
        """
        # Try to parse if the LLM output is already JSON
        try:
            data = json.loads(self.raw_text)
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass

        # Fallback: parse plain text into JSON
        cases = []
        test_case_blocks = re.split(r"\n\s*\n", self.raw_text)  # split by blank lines

        for idx, block in enumerate(test_case_blocks, start=1):
            lines = [line.strip("-• ") for line in block.split("\n") if line.strip()]
            if not lines:
                continue

            title = lines[0]
            steps = []
            expected = ""

            for line in lines[1:]:
                if line.lower().startswith("expected"):
                    expected = line.split(":", 1)[-1].strip()
                else:
                    steps.append(line)

            cases.append({
                "id": f"TC-{idx:03}",
                "title": title,
                "steps": steps,
                "expected": expected
            })

        return cases

    def to_csv(self, file_path: str = None) -> Union[str, None]:
        """
        Exports test cases to CSV in step-by-step format.

        If file_path is provided → saves to file.
        If not provided → returns CSV string.
        """
        json_data = self.to_json()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["TestCaseID", "Title", "Step No", "Step Description", "Expected Result"])

        for case in json_data:
            for step_no, step in enumerate(case["steps"], start=1):
                expected = case["expected"] if step_no == len(case["steps"]) else ""
                writer.writerow([case["id"], case["title"], step_no, step, expected])

        csv_content = output.getvalue()
        output.close()

        if file_path:
            with open(file_path, "w", encoding="utf-8", newline="") as f:
                f.write(csv_content)
            print(f"📄 CSV file saved: {file_path}")
            return None
        else:
            return csv_content

    def to_text(self) -> str:
        """
        Returns test cases as human-readable text.
        """
        json_data = self.to_json()
        output = []
        for case in json_data:
            output.append(f"{case['id']}: {case['title']}")
            for step in case["steps"]:
                output.append(f"  - {step}")
            output.append(f"Expected: {case['expected']}")
            output.append("")
        return "\n".join(output)
    
    def to_excel(self, file_path: str):
        """
        Exports test cases to an Excel file.
        """
        json_data = self.to_json()
        wb = Workbook()
        ws = wb.active
        ws.title = "Test Cases"

        # Header row
        ws.append(["Test Case ID", "Title", "Steps", "Expected Result"])

        for case in json_data:
            ws.append([
                case["id"],
                case["title"],
                " | ".join(case["steps"]),
                case["expected"]
            ])

        wb.save(file_path)
        print(f"📄 Excel file saved: {file_path}")

# Example usage
if __name__ == "__main__":
    raw_output = """
    1. Login with valid credentials
    - Step 1: Open login page
    - Step 2: Enter valid username and password
    - Step 3: Click Login
    Expected: User is redirected to dashboard

    2. Login with invalid password
    - Step 1: Open login page
    - Step 2: Enter valid username and invalid password
    - Step 3: Click Login
    Expected: Error message is displayed
    """
    formatter = TestCaseFormatter(raw_output)
    print("JSON Output:", json.dumps(formatter.to_json(), indent=2))
    print("\nCSV Data:", formatter.to_csv_list())
    print("\nPlain Text:\n", formatter.to_text())
    formatter.to_excel("test_cases.xlsx")
