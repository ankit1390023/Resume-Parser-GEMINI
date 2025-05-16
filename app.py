# FLASK APP - Run the app using flask --app app.py run
import os, sys
from flask import Flask, request, jsonify
from flask_cors import CORS
from pypdf import PdfReader 
import json
import re
from resumeparser import ats_extractor
from ats_score_checker import get_ats_score
from werkzeug.utils import secure_filename

# Get the absolute path of the project directory
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_PATH = os.path.join(PROJECT_DIR, "__DATA__")

# Create __DATA__ directory if it doesn't exist
os.makedirs(UPLOAD_PATH, exist_ok=True)

app = Flask(__name__)
# Configure CORS to allow requests from the frontend
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite's default ports
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_ats_score(analysis_text):
    """Extract the ATS score from the analysis text."""
    try:
        # Look for the overall score line
        score_match = re.search(r'Overall ATS Score:\s*(\d+)', analysis_text)
        if score_match:
            return int(score_match.group(1))
        
        # Fallback: try to find any number between 0-100 that appears to be a score
        score_match = re.search(r'(\d+)\s*out of\s*100', analysis_text)
        if score_match:
            return int(score_match.group(1))
        
        return 0
    except:
        return 0

def extract_suggestions(analysis_text):
    """Extract improvement suggestions from the analysis text."""
    suggestions = []
    try:
        # Look for sections that contain suggestions
        suggestion_sections = re.findall(r'(?:Suggestion|Recommendation|Improvement)[^:]*:(.*?)(?=\n\n|\Z)', analysis_text, re.DOTALL | re.IGNORECASE)
        
        for section in suggestion_sections:
            # Split into individual suggestions
            items = re.findall(r'[-•*]\s*(.*?)(?=\n[-•*]|\Z)', section, re.DOTALL)
            suggestions.extend([item.strip() for item in items if item.strip()])
        
        # If no suggestions found in structured format, try to find any sentence that looks like a suggestion
        if not suggestions:
            suggestion_sentences = re.findall(r'(?:should|could|recommend|suggest|improve|add|include)[^.]*\.', analysis_text, re.IGNORECASE)
            suggestions.extend([s.strip() for s in suggestion_sentences if s.strip()])
        
        return suggestions
    except:
        return []

@app.route('/')
def index():
    return jsonify({"message": "Resume Parser API is running"})

@app.route("/parse-resume", methods=["POST"])
def parse_resume():
    try:
        # Check if file is present in request
        if 'file' not in request.files:
            return jsonify({
                'error': 'No file provided',
                'details': 'Please upload a PDF file'
            }), 400

        file = request.files['file']
        
        # Check if file is empty
        if file.filename == '':
            return jsonify({
                'error': 'No file selected',
                'details': 'Please select a PDF file to upload'
            }), 400

        # Check if file is allowed
        if not allowed_file(file.filename):
            return jsonify({
                'error': 'Invalid file type',
                'details': 'Only PDF files are allowed'
            }), 400

        # Save file securely
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Parse the resume
        result = ats_extractor(filepath)

        # Clean up - remove the file after processing
        try:
            os.remove(filepath)
        except Exception as e:
            print(f"Error removing file {filepath}: {str(e)}")

        return result

    except Exception as e:
        return jsonify({
            'error': 'Failed to process resume',
            'details': str(e)
        }), 500

@app.route("/process", methods=["POST"])
def ats():
    try:
        if 'pdf_doc' not in request.files:
            return jsonify({
                "error": "No file provided",
                "message": "Please upload a PDF file"
            }), 400

        doc = request.files['pdf_doc']
        if doc.filename == '':
            return jsonify({
                "error": "No file selected",
                "message": "Please select a PDF file"
            }), 400

        if not doc.filename.lower().endswith('.pdf'):
            return jsonify({
                "error": "Invalid file type",
                "message": "Only PDF files are supported"
            }), 400

        # Save the file
        doc_path = os.path.join(UPLOAD_PATH, "file.pdf")
        doc.save(doc_path)

        # Read and process the file
        try:
            data = _read_file_from_path(doc_path)
        except Exception as e:
            return jsonify({
                "error": "Failed to read PDF file",
                "message": str(e)
            }), 400

        # Get ATS analysis
        try:
            ats_analysis = get_ats_score(data)
            ats_score = extract_ats_score(ats_analysis)
            suggestions = extract_suggestions(ats_analysis)
            
            result = {
                "ats_score": ats_score,
                "suggestions": suggestions
            }
            
            return jsonify(result)
        except Exception as e:
            return jsonify({
                "error": "Failed to process resume",
                "message": str(e)
            }), 500
    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "An error occurred while processing your resume"
        }), 500
    finally:
        # Clean up the uploaded file
        try:
            if os.path.exists(doc_path):
                os.remove(doc_path)
        except:
            pass
 
def _read_file_from_path(path):
    reader = PdfReader(path) 
    data = ""

    for page_no in range(len(reader.pages)):
        page = reader.pages[page_no] 
        data += page.extract_text()

    return data 

if __name__ == "__main__":
    app.run(port=8000, debug=True)

