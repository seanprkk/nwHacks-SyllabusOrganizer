import os
import google.generativeai as genai


def analyze_pdf(file_path, prompt):
    # 2. Upload the file to the File API
    print(f"Uploading file: {file_path}...")
    sample_pdf = genai.upload_file(file_path, mime_type="application/pdf")
    
    print(f"File uploaded. URI: {sample_pdf.uri}")

    # 3. Select the model (Gemini 1.5 Flash is efficient for documents)
    model = genai.GenerativeModel("gemini-1.5-flash")

    # 4. Generate content using the prompt and the uploaded file
    print("Generating content...")
    response = model.generate_content([prompt, sample_pdf])

    # 5. Print the response
    print("\nResponse:")
    print(response.text)

    # Optional: Delete the file from the cloud after use to manage storage
    # sample_pdf.delete()

# Example Usage:
# Ensure you have a file named 'sample_document.pdf' in the same folder
# analyze_pdf("sample_document.pdf", "Summarize this document in 3 bullet points.")