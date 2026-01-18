from google import genai
from google.genai import types
import os
import json
import time

# --- Configuration ---
# Set your API key here or in the environment
API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyBr6YefUZQkwJmd0d4jj54DgaNoc-uoPMc") 

PDF_FILENAME = "docs/cpsc330-2025W1_README.pdf" 
OUTPUT_JSON_FILE = "data/syllabus-info.json"

# --- PROMPT ---
PROMPT = """
You are a data extraction assistant. Analyze the attached course syllabus PDF.
Extract the course information and strictly output valid JSON in the following format:

{
    "course-info": {
        "code": "ex. Cpsc 330",
        "title": "ex. Applied Machine Learning",
        "location": "ex. DMP 310",
        "resources": [
            { "name": "ex. Piazza", "link": "ex. piazza.com" }
        ],
        "contacts": [
            { "name": "ex. Mr. Steph", "position": "ex. instructor", "email": "ex. gtoti@cs.ubc.ca" }
        ],
        "homework": [
            { 
                "name": "ex. Hw1",
                "due-date": "ex. 2025-09-09T23:59:00", 
                "links": "ex. Gradescope link" 
            }
        ],
        "meetings": [
            {
                "type": "ex. lecture/lab/tutorial",
                "lead": "ex. Mr. Steph",
                "day": "tuesday",
                "start_time": "ex. 15:30:00",
                "end_time": "ex. 16:50:00",
                "location": "DMP 310"
            }
        ],
        "Important-dates": [
            {
                "name": "ex. Holiday/Midterm 1",
                "day": "tuesday",
                "notes": "ex. Information TBA"
            }
        ]
    }
}

If a specific field is not found, leave it as null or an empty string.
Ensure dates are in ISO8601 format where possible.
Don't include TAs as contacts.
Include the embedded links in the pdf under resources whenever possible.
"""

def main():
    client = genai.Client(api_key=API_KEY)

    if not os.path.exists(PDF_FILENAME):
        print(f"Error: The file '{PDF_FILENAME}' was not found.")
        return

    # Ensure output directory exists
    output_dir = os.path.dirname(OUTPUT_JSON_FILE)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        print(f"Uploading {PDF_FILENAME} to Gemini...")
        
        # --- FIX IS HERE: use 'file=' instead of 'path=' ---
        pdf_file = client.files.upload(file=PDF_FILENAME)
        
        print(f"Upload complete. File URI: {pdf_file.uri}")

        while pdf_file.state.name == "PROCESSING":
            print("Processing file...")
            time.sleep(2)
            pdf_file = client.files.get(name=pdf_file.name)

        if pdf_file.state.name == "FAILED":
            raise ValueError("File processing failed.")

        print("Analyzing document and generating JSON...")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[PROMPT, pdf_file],
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        json_content = response.text
        parsed_data = json.loads(json_content)
        
        with open(OUTPUT_JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(parsed_data, f, indent=4)

        print(f"\nSuccess! Data saved to: {OUTPUT_JSON_FILE}")

    except Exception as e:
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    main()