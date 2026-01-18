# gemini_processor.py - OpenRouter API processing logic
import os
import json
import base64
import requests

# Configuration
# API_KEY = os.getenv("OPENROUTER_API_KEY", "<openrouter.ai-key>")
API_KEY = "open router api key"
OUTPUT_JSON_FILE = "data/syllabus-info.json"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

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
                "location": "ex. Information TBA"
            }
        ]
    }
}

If a specific field is not found, leave it as "N/A".
Ensure dates are in ISO8601 format where possible.
Don't include TAs as contacts.
Include the embedded links in the pdf under resources whenever possible.

Output ONLY the JSON, no additional text or markdown formatting.
"""

def process_pdf_with_gemini(pdf_data, selected_template):
    """
    Process PDF with Gemini via OpenRouter API and return extracted data
    
    Args:
        pdf_data: Binary PDF data
        selected_template: Template name (for future use)
    
    Returns:
        tuple: (extracted_data, error, output_file)
    """
    try:
        # Convert PDF to base64
        print("Converting PDF to base64...")
        pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
        
        # Prepare the API request
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5000",  # Optional: your site URL
            "X-Title": "Syllabus Processor"  # Optional: your app name
        }
        
        payload = {
            "model": "google/gemini-2.0-flash-exp:free",  # Free Gemini model on OpenRouter
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": PROMPT
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:application/pdf;base64,{pdf_base64}"
                            }
                        }
                    ]
                }
            ],
            "response_format": {
                "type": "json_object"
            }
        }
        
        # Make the API request
        print("Sending request to OpenRouter (Gemini)...")
        response = requests.post(
            OPENROUTER_API_URL,
            headers=headers,
            json=payload,
            timeout=120
        )
        
        response.raise_for_status()
        result = response.json()
        
        # Extract the JSON content from the response
        print("Parsing response...")
        json_content = result['choices'][0]['message']['content']
        
        # Try to parse the JSON (handle potential markdown code blocks)
        json_content = json_content.strip()
        if json_content.startswith('```'):
            # Remove markdown code blocks if present
            lines = json_content.split('\n')
            json_content = '\n'.join(lines[1:-1]) if len(lines) > 2 else json_content
        
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
    
    except requests.exceptions.RequestException as e:
        error_msg = f"API request failed: {str(e)}"
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                error_msg += f" - {error_detail}"
            except:
                error_msg += f" - {e.response.text}"
        print(f"Error: {error_msg}")
        return None, error_msg, None
    
    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse JSON response: {str(e)}"
        print(f"Error: {error_msg}")
        return None, error_msg, None
    
    except Exception as e:
        error_msg = f"Unexpected error processing PDF: {str(e)}"
        print(f"Error: {error_msg}")
        return None, error_msg, None