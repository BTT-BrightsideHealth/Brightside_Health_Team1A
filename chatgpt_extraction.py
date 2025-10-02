# file: chatgpt_extraction.py
import os, pathlib
from openai import OpenAI

MODEL = "gpt-4.1"  # Pro model

SYSTEM_PROMPT = """
You are an information extraction system. Your task is to identify and extract key entities and the relationships between them from clinical research text. Focus only on what is 
explicitly stated in the text. Do not infer or add extra information. The final output must be valid JSON and nothing else.

Entities to Extract:
- medical_condition: a mental health disorder or subtype (e.g., “major depressive disorder”, “anxious depression”)
- medication: a specific drug or class of drugs (e.g., “sertraline”, “SSRIs”)
- treatment_type: a non-drug treatment or therapy (e.g., “psychotherapy”, “electroconvulsive therapy”)
- outcome: a measurable result (e.g., “efficacy”, “remission”, “side effects”, “dropout”)
- patient_group: a group with shared traits (e.g., “adolescents”, “outpatients”, “anxious patients”)
- study: a trial type or named study (e.g., “STAR*D”, “randomized controlled trial”)
- measure: a clinical scale/metric (e.g., “Hamilton Depression Rating Scale (HDRS)”)
- dosage: medication dosage info

Relationships to Extract:
- treats: medication/treatment_type → medical_condition
- has_outcome: medication/treatment_type/patient_group → outcome
- compares: study → ≥2 medication/treatment_type
- affects: patient_group → outcome
- has_dosage: medication → dosage
- measured_by: outcome → measure

Output format:
Return ONLY a single JSON object:
{
  "entities": [ { "id": int, "text": string, "type": string }, ... ],
  "relationships": [ { "head": int, "tail": int, "type": string, "evidence": string }, ... ]
}
If nothing found, return: {"entities": [], "relationships": []}
"""

BASE_DIR = pathlib.Path(__file__).parent
PDF_PATH = BASE_DIR / "WJCC-9-9350.pdf"
OUT_PATH = BASE_DIR / "chatgpt_extracted.txt"

def main():
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("Set OPENAI_API_KEY in your environment.")

    client = OpenAI()

    # 1) Upload the PDF -> get file_id (ONLY place we open the file)
    with open(PDF_PATH, "rb") as f:
        uploaded = client.files.create(file=f, purpose="assistants")

    # 2) Use file_id in Responses API (DO NOT pass open(...) here)
    resp = client.responses.create(
        model=MODEL,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": [
                {"type": "input_text", "text": "Extract and clean the following PDF:"},
                {"type": "input_file", "file_id": uploaded.id}
            ]}
        ],
        temperature=0,
    )

    text_out = resp.output_text
    pathlib.Path(OUT_PATH).write_text(text_out, encoding="utf-8")
    print(f"[ok] wrote: {OUT_PATH}")

    # 3) (Optional) delete uploaded file from OpenAI
    try:
        client.files.delete(uploaded.id)
    except Exception:
        pass

if __name__ == "__main__":
    main()
