AI Resume Analyzer - Implementation Guide
This project combines a beautiful frontend interface with AI-powered resume analysis using OpenAI's API. The application provides real-time feedback on resumes, offering summary information, improvement suggestions, and job role fit analysis.

Project Structure
index.html - Frontend interface with Tailwind CSS
app.py - Flask backend server that processes resumes and communicates with OpenAI's API
requirements.txt - Python dependencies
Setup Instructions
1. Install Backend Dependencies
First, install the required Python packages:

bash
pip install -r requirements.txt
You'll also need to install some system dependencies for PDF processing:

bash
# For Ubuntu/Debian
sudo apt-get install -y poppler-utils tesseract-ocr

# For macOS
brew install poppler tesseract

# For Windows
# Download and install Poppler from: http://blog.alivate.com.au/poppler-windows/
# Download and install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
2. Set Your OpenAI API Key
Edit app.py and replace "your_openai_api_key_here" with your actual OpenAI API key:

python
api_key = "your_actual_openai_api_key"  # Replace with your actual OpenAI API key
3. Start the Backend Server
Run the Flask backend server:

bash
python app.py
This will start the server at http://localhost:5000

4. Access the Frontend
Simply open index.html in your web browser. If you're running the HTML directly from your file system, you might encounter CORS issues. In that case, you can either:

Use a simple HTTP server to serve the HTML file:
bash
# Using Python
python -m http.server 8000
Then access the app at http://localhost:8000
Or modify your browser settings to allow cross-origin requests for local files.
Usage
Upload a resume file (PDF or DOCX format)
Enter your preferred job role
Click "Analyze Resume" button
View the analysis results:
Resume Summary
Suggestions for Improvement
Role Fit & Recommendations
Customization Options
Frontend Customization
The interface uses Tailwind CSS for styling. You can modify the colors, fonts, and layout in the index.html file.

AI Prompt Customization
You can edit the system prompts in app.py to customize the AI's response style and focus areas:

python
# In the get_response function
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "YOUR CUSTOM PROMPT HERE"},
        {"role": "user", "content": prompt}
    ]
)
Additional Notes
The application uses OCR as a fallback for PDFs that cannot be parsed directly
For production use, consider implementing user authentication and securing the API key
You may want to optimize the API usage by implementing caching or rate limiting
Troubleshooting
If you encounter issues with PDF processing, ensure Poppler and Tesseract are properly installed
Check console logs for JavaScript errors
Verify that the backend server is running and accessible
License
This project is available for personal and commercial use.
