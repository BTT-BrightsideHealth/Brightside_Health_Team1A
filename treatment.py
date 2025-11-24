import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# load JSON
with open("combined-final-CHATGPT.json", "r", encoding="utf-8") as f:
    extracted_json = json.load(f)


prompt = f"""
You are a clinical information validation system.

Your input is a JSON object containing entities and relationships extracted from clinical mental health research, focusing on depression and anxiety. Each entity may be a medication, therapy, symptom, or other relevant factor.

Your task is to:

1. Analyze the JSON for any potential cross-interactions between:
   - Medications
   - Therapies
   - Other clinical factors (e.g., dietary supplements, comorbid conditions)

2. Flag interactions that are:
   - Known contraindications
   - Synergistic effects
   - Potential conflicts in treatment

3. Add a new key "interactions" in the JSON, which is a list of objects. Each object should include:
   - "entity_1": Name of first entity
   - "entity_2": Name of second entity
   - "type": Type of interaction (e.g., contraindication, synergy, conflict)
   - "source": Reference if available (if unknown, use "unknown")

Return only valid JSON and ensure it is syntactically correct.

Here is the JSON to analyze:

{json.dumps(extracted_json)}
"""

response = client.chat.completions.create(
    model="gpt-5-mini",
    messages=[
        {"role": "system", "content": "You are a clinical validation assistant."},
        {"role": "user", "content": prompt}
    ]
)


# model's output
output_text = response.choices[0].message.content.strip()


if output_text.startswith("```json"):
    output_text = output_text[len("```json"):].strip()
if output_text.endswith("```"):
    output_text = output_text[:-3].strip()

# parse JSON
try:
    validated_json = json.loads(output_text)
except json.JSONDecodeError:
    print("LLM did not return valid JSON. Raw output:")
    print(output_text)
    validated_json = None

# save validated interactions
if validated_json:
    with open("validated_interactions.json", "w", encoding="utf-8") as f:
        json.dump(validated_json, f, ensure_ascii=False, indent=2)

print("Done! Validated JSON saved to validated_interactions.json")