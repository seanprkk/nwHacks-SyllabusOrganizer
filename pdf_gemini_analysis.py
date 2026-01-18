# gemini_processor.py - Gemini API processing logic
import os
import json
import time
import tempfile
from google import genai
from google.genai import types

# Configuration
# API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyDPC-PMCvP95WVNFOMmyFqomUeAg43Eg5Q")
API_KEY=""
print(API_KEY)
OUTPUT_JSON_FILE = "data/syllabus-info.json"

# Gemini Prompt
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
            { "name": "ex. Prof. Steph", "position": "ex. instructor", "email": "ex. gtoti@cs.ubc.ca" }
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
                "lead": "ex. Prof. Steph",
                "day": "tuesday",
                "start_time": "ex. 15:30:00",
                "end_time": "ex. 16:50:00",
                "location": "DMP 310"
            }
        ],
        "Important-dates": [
            {
                "name": "ex. Holiday/Midterm 1",
                "date": "ex. 2026-01-01",
                "start_time": "ex. 15:30:00",
                "end_time": "ex. 16:50:00",
                "location": "ex. Information TBA"
            }
        ]
    }
}

If a specific field is not found, leave it as null or an empty string.
Ensure dates are in ISO8601 format where possible.
Don't include TAs as contacts.
Include the embedded links in the pdf under resources whenever possible.
"""

def process_pdf_with_gemini(pdf_data, selected_template):
    """
    Process PDF with Gemini API and return extracted data
    
    Args:
        pdf_data: Binary PDF data
        selected_template: Template name (for future use)
    
    Returns:
        tuple: (extracted_data, error, output_file)
    """
    try:
        client = genai.Client(api_key=API_KEY)
        
        # Create a temporary file to save the PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(pdf_data)
            tmp_file_path = tmp_file.name
        
        try:
            # Upload file to Gemini
            print(f"Uploading PDF to Gemini...")
            pdf_file = client.files.upload(file=tmp_file_path)
            print(f"Upload complete. File URI: {pdf_file.uri}")
            
            # Wait for processing
            while pdf_file.state.name == "PROCESSING":
                print("Processing file...")
                time.sleep(2)
                pdf_file = client.files.get(name=pdf_file.name)
            
            if pdf_file.state.name == "FAILED":
                raise ValueError("File processing failed.")
            
            # Generate content
            print("Analyzing document and generating JSON...")
            response = client.models.generate_content(
                model="gemini-flash-latest",
                contents=[PROMPT, pdf_file],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            
            # Parse JSON
            json_content = response.text
            parsed_data = json.loads(json_content)
            
            # Ensure output directory exists
            output_dir = os.path.dirname(OUTPUT_JSON_FILE)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # Save to file
            with open(OUTPUT_JSON_FILE, "w", encoding="utf-8") as f:
                json.dump(parsed_data, f, indent=4)
            
            print(f"Success! Data saved to: {OUTPUT_JSON_FILE}")
            return parsed_data, None, OUTPUT_JSON_FILE
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
    
    except Exception as e:
        print(f"Error processing PDF: {e}")
        return None, str(e), None