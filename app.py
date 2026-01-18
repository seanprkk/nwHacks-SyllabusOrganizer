# app.py - Main Flask application
from flask import Flask, render_template_string, request, send_file, jsonify
import os
import json
from pdf_gemini_analysis import process_pdf_with_gemini
from populate_template import populate_markdown_template
from notion_importer import import_to_notion

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Syllaboss</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 12px;
            padding: 40px;
            max-width: 500px;
            width: 100%;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        h1 {
            color: #333;
            margin-bottom: 30px;
            text-align: center;
            font-size: 28px;
        }
        .form-group {
            margin-bottom: 25px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 500;
            font-size: 14px;
        }
        .file-input-wrapper {
            position: relative;
            overflow: hidden;
            display: inline-block;
            width: 100%;
        }
        .file-input-wrapper input[type=file] {
            position: absolute;
            left: -9999px;
        }
        .file-input-label {
            display: block;
            padding: 12px 20px;
            background: #f5f5f5;
            border: 2px dashed #ccc;
            border-radius: 8px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }
        .file-input-label:hover {
            background: #efefef;
            border-color: #667eea;
        }
        .file-name {
            margin-top: 10px;
            color: #667eea;
            font-size: 14px;
            font-weight: 500;
        }
        .template-options {
            display: flex;
            gap: 12px;
        }
        .template-option {
            flex: 1;
        }
        .template-option input[type=radio] {
            display: none;
        }
        .template-option label {
            display: block;
            padding: 15px;
            background: #f5f5f5;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            margin: 0;
        }
        .template-option input[type=radio]:checked + label {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }
        .template-option label:hover {
            border-color: #667eea;
        }
        input[type=text] {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
        }
        input[type=text]:focus {
            outline: none;
            border-color: #667eea;
        }
        small {
            color: #666;
            font-size: 12px;
            margin-top: 5px;
            display: block;
        }
        small a {
            color: #667eea;
            text-decoration: none;
        }
        small a:hover {
            text-decoration: underline;
        }
        button[type=submit] {
            width: 100%;
            padding: 14px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.3s;
        }
        button[type=submit]:hover {
            background: #5568d3;
        }
        button[type=submit]:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        .success-message {
            background: #d4edda;
            color: #155724;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border: 1px solid #c3e6cb;
        }
        .success-message a {
            color: #155724;
            font-weight: bold;
            text-decoration: underline;
        }
        .error-message {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border: 1px solid #f5c6cb;
        }
        .processing-message {
            background: #fff3cd;
            color: #856404;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border: 1px solid #ffeaa7;
        }
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        pre {
            background: #f5f5f5;
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
            font-size: 12px;
            max-height: 400px;
            overflow-y: auto;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Syllaboss</h1>
        <h1>Upload Course Syllabus</h1>
        <h1>... and get a beautiful Notion summary!</h1>
        
        {% if success %}
        <div class="success-message">
            ✓ Syllabus processed successfully!<br>
            Template: {{ template }}<br>
            {% if notion_url %}
            <strong>Notion Page:</strong> <a href="{{ notion_url }}" target="_blank">Open in Notion</a><br>
            {% endif %}
        </div>
        {% endif %}
        
        {% if error %}
        <div class="error-message">
            ✗ Error: {{ error }}
        </div>
        {% endif %}
        
        <form method="POST" enctype="multipart/form-data" id="uploadForm">
            <div class="form-group">
                <label>Select Template</label>
                <div class="template-options">
                    <div class="template-option">
                        <input type="radio" id="modern" name="template" value="modern" checked>
                        <label for="modern">Modern</label>
                    </div>
                    <div class="template-option">
                        <input type="radio" id="classic" name="template" value="classic">
                        <label for="classic">Classic</label>
                    </div>
                    <div class="template-option">
                        <input type="radio" id="basic" name="template" value="basic">
                        <label for="basic">Basic</label>
                    </div>
                </div>
            </div>
            
            <div class="form-group">
                <label>Upload PDF Syllabus</label>
                <div class="file-input-wrapper">
                    <input type="file" id="pdfFile" name="pdf_file" accept=".pdf" required>
                    <label for="pdfFile" class="file-input-label">
                        <span id="fileText">Choose PDF file...</span>
                    </label>
                </div>
                <div id="fileName" class="file-name"></div>
            </div>
            
            <div class="form-group">
                <label>Notion API Key (Optional)</label>
                <input type="text" name="notion_api_key" placeholder="ntn_...">
                <small>Get your integration token from <a href="https://www.notion.so/my-integrations" target="_blank">notion.so/my-integrations</a></small>
            </div>
            
            <button type="submit" id="submitBtn">Upload & Process Syllabus</button>
        </form>
        
        <div id="processingIndicator" style="display: none;">
            <div class="processing-message">
                Processing your syllabus with Gemini AI...
            </div>
            <div class="spinner"></div>
        </div>
        
        <div id="successMessage" style="display: none;" class="success-message">
            ✓ Syllabus processed successfully!<br>
            <span id="successDetails"></span>
        </div>
    </div>
    
    <script>
        const fileInput = document.getElementById('pdfFile');
        const fileText = document.getElementById('fileText');
        const fileName = document.getElementById('fileName');
        const form = document.getElementById('uploadForm');
        const submitBtn = document.getElementById('submitBtn');
        const processingIndicator = document.getElementById('processingIndicator');
        const successMessage = document.getElementById('successMessage');
        const successDetails = document.getElementById('successDetails');
        
        fileInput.addEventListener('change', function(e) {
            if (this.files && this.files[0]) {
                const file = this.files[0];
                fileText.textContent = '✓ File selected';
                fileName.textContent = file.name;
            } else {
                fileText.textContent = 'Choose PDF file...';
                fileName.textContent = '';
            }
        });
        
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            submitBtn.disabled = true;
            submitBtn.textContent = 'Processing...';
            processingIndicator.style.display = 'block';
            successMessage.style.display = 'none';
            
            const formData = new FormData(form);
            
            try {
                const response = await fetch('/process', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    // Hide processing indicator
                    processingIndicator.style.display = 'none';
                    
                    // Show success message
                    successMessage.style.display = 'block';
                    
                    if (result.notion_url) {
                        successDetails.innerHTML = `
                            Template: ${result.template}<br>
                            <strong>Notion Page:</strong> <a href="${result.notion_url}" target="_blank">Open in Notion</a>
                        `;
                    } else if (result.download_url) {
                        successDetails.innerHTML = `
                            Template: ${result.template}<br>
                            <strong>Downloading markdown file...</strong>
                        `;
                        
                        // Trigger download
                        const a = document.createElement('a');
                        a.href = result.download_url;
                        a.download = 'course-syllabus.md';
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        
                        // Reset form after 2 seconds
                        setTimeout(() => {
                            resetForm();
                        }, 2000);
                    }
                } else {
                    throw new Error(result.error || 'Processing failed');
                }
            } catch (error) {
                processingIndicator.style.display = 'none';
                alert('Error: ' + error.message);
                resetForm();
            }
        });
        
        function resetForm() {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Upload & Process Syllabus';
            form.reset();
            fileText.textContent = 'Choose PDF file...';
            fileName.textContent = '';
            successMessage.style.display = 'none';
        }
    </script>
</body>
</html>
'''

@app.route('/', methods=['GET'])
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/process', methods=['POST'])
def process():
    """Handle the actual processing and return JSON response"""
    try:
        # Get selected template
        selected_template = request.form.get('template', 'modern')
        notion_api_key = request.form.get('notion_api_key', '').strip()
        
        # Get uploaded file
        if 'pdf_file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'})
        
        file = request.files['pdf_file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        if not file.filename.endswith('.pdf'):
            return jsonify({'success': False, 'error': 'File must be a PDF'})
        
        # Read the file data
        pdf_data = file.read()
        
        # Process with Gemini
        extracted_data, error, output_file = process_pdf_with_gemini(pdf_data, selected_template)
        
        if error:
            return jsonify({'success': False, 'error': f'Failed to process PDF: {error}'})
        
        # Populate markdown template
        template_path = f'notion_templates/notion_template_{selected_template}.md'
        markdown_output = 'output/filled-in-template.md'
        os.makedirs('output', exist_ok=True)
        
        if not os.path.exists(template_path):
            return jsonify({'success': False, 'error': 'Template not found'})
        
        markdown_content = populate_markdown_template(output_file, template_path, markdown_output)
        
        # Import to Notion if API key provided
        if notion_api_key:
            success, notion_url, notion_error = import_to_notion(markdown_content, notion_api_key)
            if not success:
                return jsonify({'success': False, 'error': f'Notion import failed: {notion_error}'})
            
            return jsonify({
                'success': True,
                'template': selected_template,
                'notion_url': notion_url
            })
        else:
            # Return download URL instead of sending file directly
            return jsonify({
                'success': True,
                'template': selected_template,
                'download_url': '/download'
            })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download')
def download():
    """Serve the generated markdown file"""
    markdown_output = 'output/filled-in-template.md'
    if os.path.exists(markdown_output):
        return send_file(markdown_output, as_attachment=True, download_name='course-syllabus.md')
    else:
        return "File not found", 404

if __name__ == '__main__':
    app.run(debug=True)