# main.py
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import google.generativeai as genai
import os
import PyPDF2 as pdf
from dotenv import load_dotenv
import json

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="."), name="static")

load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)


def get_gemini_response(input_text):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(input_text)
    return response.text


def input_pdf_text(file):
    reader = pdf.PdfReader(file)
    text = ""
    for page in range(len(reader.pages)):
        page = reader.pages[page]
        text += str(page.extract_text())
    return text


input_prompt = """
Hey Act Like a skilled or very experience ATS(Application Tracking System)
with a deep understanding of tech field,software engineering,data science ,data analyst
and big data engineer. Your task is to evaluate the resume based on the given job description.
You must consider the job market is very competitive and you should provide 
best assistance for improving thr resumes. Assign the percentage Matching based 
on Jd and
the missing keywords with high accuracy
resume:{text}
description:{jd}

I want the response in one single string having the structure
{{"JD Match":"%","MissingKeywords:[]","Profile Summary":""}}
"""


@app.get("/")
async def read_root():
    return FileResponse('index.html')


@app.post("/analyze")
async def analyze_resume(file: UploadFile = File(..., alias="resume"), jd: str = Form(...)):
    try:
        if not file.filename.endswith('.pdf'):
            return {"error": "Please upload a PDF file"}

        contents = await file.read()
        # Save temporarily to process with PyPDF2
        temp_path = "temp.pdf"
        with open(temp_path, "wb") as f:
            f.write(contents)

        try:
            text = input_pdf_text(temp_path)
            response = get_gemini_response(input_prompt.format(text=text, jd=jd))
            return json.loads(response)
        except Exception as e:
            return {"error": f"Processing error: {str(e)}"}
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)

    except Exception as e:
        return {"error": f"Upload error: {str(e)}"}