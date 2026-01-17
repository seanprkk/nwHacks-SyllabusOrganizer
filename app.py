from flask import Flask, render_template_string, request, redirect, url_for
import os

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Store uploaded file data in memory (in production, use a database)
uploaded_pdf = None
selected_template = None

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Syllabus Upload</title>
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
    </style>
</head>
<body>
    <div class="container">
        <h1>Upload Course Syllabus</h1>
        
        {% if success %}
        <div class="success-message">
            ✓ Syllabus uploaded successfully!<br>
            Template: {{ template }}<br>
            File size: {{ file_size }} bytes
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
                        <input type="radio" id="library" name="template" value="library">
                        <label for="library">Library</label>
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
            
            <button type="submit">Upload Syllabus</button>
        </form>
    </div>
    
    <script>
        const fileInput = document.getElementById('pdfFile');
        const fileText = document.getElementById('fileText');
        const fileName = document.getElementById('fileName');
        
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
    </script>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def upload():
    global uploaded_pdf, selected_template
    
    if request.method == 'POST':
        # Get selected template
        selected_template = request.form.get('template', 'modern')
        
        # Get uploaded file
        if 'pdf_file' not in request.files:
            return redirect(request.url)
        
        file = request.files['pdf_file']
        
        if file.filename == '':
            return redirect(request.url)
        
        if file and file.filename.endswith('.pdf'):
            # Store the file data in memory
            uploaded_pdf = file.read()
            
            return render_template_string(
                HTML_TEMPLATE, 
                success=True, 
                template=selected_template,
                file_size=len(uploaded_pdf)
            )
    
    return render_template_string(HTML_TEMPLATE, success=False)

if __name__ == '__main__':
    app.run(debug=True)