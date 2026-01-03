from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from openai import OpenAI
import PyPDF2
from docx import Document
import os
import tempfile
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Set OpenAI API Key
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def extract_text_from_resume(file):
    text = ""
    filename = file.filename
    
    # Create a temporary file to handle the upload
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        file.save(temp_file.name) # Save explicitly to handle stream position
        temp_path = temp_file.name
    
    try:
        if filename.lower().endswith('.pdf'):
            try:
                reader = PyPDF2.PdfReader(temp_path)
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted
            except Exception as e:
                print(f"PDF Error: {e}")
                
        elif filename.lower().endswith('.docx'):
            try:
                doc = Document(temp_path)
                text = '\n'.join(para.text for para in doc.paragraphs)
            except Exception as e:
                print(f"DOCX Error: {e}")
        else:
            return None # Unsupported format
            
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    return text.strip()

def clean_markdown(text):
    import re
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
        
        # ERROR HANDLING FOR SCANNED PDFS
        if resume_text is None:
             return jsonify({"error": "Unsupported file format. Please upload PDF or DOCX."}), 400
             
        if not resume_text:
            return jsonify({"error": "Could not read text. If this is a scanned PDF (image), it is not supported in this lightweight version. Please upload a text-based PDF."}), 400

        def get_response(prompt):
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional resume reviewer who gives honest career advice. Keep it professional but direct."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content.strip()

        # Generate Prompts
        summary_prompt = f"Summarize this resume in 3-4 lines:\n\n{resume_text}"
        improvement_prompt = f"Identify 3 key areas for improvement in this resume (be specific):\n\n{resume_text}"
        jobmatch_prompt = f"The user applies for '{preferred_role}'. Does this resume fit? Explain briefly:\n\n{resume_text}"

        # Get AI Responses
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
    
@app.route('/')
def home():
    # The '.' means "look in the current directory"
    return send_from_directory('.', 'index.html')

# Vercel requires the app to be available as a variable
if __name__ == '__main__':
    app.run(debug=True, port=5000)