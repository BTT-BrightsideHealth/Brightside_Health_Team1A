# run_extraction.py
import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from extract.prompt_config import EXTRACTION_PROMPT

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

#Test text input (replace later with PDF text)
text = """
Sertraline was effective in treating major depression.
It improved remission rates.
The randomized controlled trial compared Sertraline and Fluoxetine.
"""

#Call OpenAI with your system prompt + input
response = client.chat.completions.create(
    model="gpt-4o-mini",   # good balance of cost/speed/accuracy
    messages=[
        {"role": "system", "content": EXTRACTION_PROMPT},
        {"role": "user", "content": text}
    ],
    temperature=0
)

#Parse output
raw_output = response.choices[0].message.content

try:
    data = json.loads(raw_output)
    print(json.dumps(data, indent=2))
except json.JSONDecodeError:
    print("⚠️ Model returned invalid JSON. Raw output:\n", raw_output)
