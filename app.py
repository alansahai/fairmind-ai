from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import PyPDF2
from docx import Document
import pytesseract
from pdf2image import convert_from_bytes
import re
import os
import tempfile
from PIL import Image

# # Set paths to executables (update these paths to match your installation)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# poppler_path = r'C:\Program Files\poppler\bin'  # Update this to your Poppler path

# images = convert_from_bytes(file_content, poppler_path=poppler_path)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Set OpenAI API Key
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# Extract text from file (PDF or DOCX, with OCR fallback)
def extract_text_from_resume(file):
    text = ""
    filename = file.filename
    file_content = file.read()
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(file_content)
        temp_path = temp_file.name
    
    try:
        if filename.endswith('.pdf'):
            try:
                # First try PyPDF2
                reader = PyPDF2.PdfReader(temp_path)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text
            except:
                pass

            # Fallback to OCR if PyPDF2 fails or text is empty
            if not text.strip():
                images = convert_from_bytes(file_content)
                for image in images:
                    text += pytesseract.image_to_string(image)

        elif filename.endswith('.docx'):
            doc = Document(temp_path)
            text = '\n'.join(para.text for para in doc.paragraphs)
        else:
            return "Unsupported file format. Please upload a PDF or DOCX."
    finally:
        # Clean up the temporary file
        os.unlink(temp_path)
    
    return text.strip()

# Remove markdown/bullet styling from AI output
def clean_markdown(text):
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'^[\-\*\d\.]+\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{2,}', '\n\n', text)
    return text.strip()

@app.route('/analyze', methods=['POST'])
def analyze_resume():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    preferred_role = request.form.get('preferredRole', '')
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if not preferred_role:
        return jsonify({"error": "Preferred role is required"}), 400
    
    try:
        resume_text = extract_text_from_resume(file)
        if not resume_text or resume_text.startswith("Unsupported"):
            return jsonify({"error": resume_text}), 400

        def get_response(prompt):
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional resume reviewer who gives honest and useful career advice in clean paragraphs. Don't be overly generic. Only suggest improvements for weak areas. Address the candidate directly like 'You should...', 'Consider revising...'. Avoid listing all resume sections unless needed."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content.strip()

        summary_prompt = f"Summarize the following resume clearly and briefly in 3–4 lines:\n\n{resume_text}"
        improvement_prompt = (
            f"Review this resume and identify only the sections that need improvement. "
            f"Write in paragraph format, addressing the candidate directly (e.g., 'You should...', 'Consider revising...'). "
            f"Do not praise or mention sections that are already strong. Focus only on what needs better structure, clarity, grammar, or relevance:\n\n{resume_text}"
        )
        jobmatch_prompt = (
            f"The user wants to apply for the role: '{preferred_role}'. Determine if this resume fits that role. "
            f"If yes, explain briefly why. If not, explain the gaps clearly and suggest 2–3 better-suited roles with justification. "
            f"Write everything in paragraph form:\n\n{resume_text}"
        )

        summary = clean_markdown(get_response(summary_prompt))
        improvement = clean_markdown(get_response(improvement_prompt))
        job_match = clean_markdown(get_response(jobmatch_prompt))

        return jsonify({
            "summary": summary,
            "improvement": improvement,
            "jobmatch": job_match
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)