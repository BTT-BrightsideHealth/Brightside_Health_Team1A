# run_extraction.py
import os
import json
import pdfplumber
from dotenv import load_dotenv
from openai import OpenAI
from extract.prompt_config import EXTRACTION_PROMPT

# 1. Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 2. Pick a PDF file to test
PDF_PATH = "data/fava-et-al-2008-difference-in-treatment-outcome-in-outpatients-with-anxious-versus-nonanxious-depression-a-star_d-report.pdf"

def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:  # avoid None errors
                text += page_text + "\n"
    return text

# 3. Read PDF text
text = extract_text_from_pdf(PDF_PATH)

# 4. Call OpenAI with your system prompt + input
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": EXTRACTION_PROMPT},
        {"role": "user", "content": text}
    ],
    temperature=0
)

# 5. Parse output
raw_output = response.choices[0].message.content

try:
    data = json.loads(raw_output)
    print(json.dumps(data, indent=2))
except json.JSONDecodeError:
    print("⚠️ Model returned invalid JSON. Raw output:\n", raw_output)
