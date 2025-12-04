import os
import json
import argparse

from openai import OpenAI
from pypdf import PdfReader  # pip install pypdf

# System Prompt
SYSTEM_PROMPT = """
You are a "Maximum Yield" Medical Extraction Engine.

Your goal is to extract a Knowledge Graph with the HIGHEST POSSIBLE number of valid interactions.
You must adopt a "Zero-Filter" policy regarding interaction significance: if there is a theoretical, mechanistic, or protocol-based reason why two things interact, YOU MUST LIST IT.

Output a SINGLE JSON object.

=========================================================
1) ENTITIES (STRICT SCHEMA)
=========================================================
Extract entities into a list of objects with unique integer IDs.
Include ALL:
- "medication": (e.g., "fluoxetine", "sertraline")
- "treatment_type": (e.g., "CBT", "ECT", "rTMS", "EMDR", "Psychodynamic Therapy")
- "medical_condition", "outcome", "measure", "patient_group"

Format:
[
  { "id": 1, "text": "fluoxetine", "type": "medication" },
  { "id": 2, "text": "CBT", "type": "treatment_type" }
]

=========================================================
2) RELATIONSHIPS
=========================================================
Standard explicit relationships found in the text.
Format: { "head": 1, "tail": 2, "type": "treats", "evidence": "..." }

=========================================================
3) INTERACTIONS (MAXIMALIST MODE)
=========================================================
**INSTRUCTION:** Cross-reference EVERY entity of type "medication" and "treatment_type" against every other one.
You must output an interaction for ANY of the following categories. Do not omit "minor" or "theoretical" risks.

**CATEGORY A: PHARMACOLOGIC CLASHES (The usual stuff)**
- **Serotonin/Norepinephrine:** Any two drugs affecting these neurotransmitters.
- **Seizure Threshold:** Bupropion, TCAs, Clozapine, Tramadol, etc.
- **Metabolic:** CYP450 inhibitors + substrates.
- **Sedation:** Any two agents with sedative properties.

**CATEGORY B: THERAPEUTIC FRICTION (Therapy-Therapy & Drug-Therapy)**
- **Interference with Learning:** Sedatives (Benzos/Z-drugs) + Psychotherapy (CBT/Exposure). *Mechanism: Impaired emotional learning/habituation.*
- **Conflicting Modalities:** Directive therapies (CBT) + Non-directive therapies (Psychoanalysis) concurrently. *Mechanism: Conflicting patient instructions.*
- **Somatic Overload:** Multiple brain stimulation therapies (ECT + rTMS + DBS) concurrently. *Mechanism: Excessive neural stimulation/unknown safety profile.*
- **Protocol Clashes:** Therapies requiring alert states vs. sedating medications.

**CATEGORY C: PHYSIOLOGICAL BURDEN**
- **Cardiovascular:** Stimulants + Cardiovascular active drugs.
- **Anticholinergic Load:** Any cumulative anticholinergic burden (TCAs + Antipsychotics + Antihistamines).

**OUTPUT RULES:**
- **Goal:** 20-40 interactions for complex texts.
- **Format:**
  {
    "id": <int>,
    "entity_ids": [<int>, <int>],
    "interaction_type": "use_with_caution" (or "contraindicated"),
    "note": "Short explanation of the clash.",
    "evidence": "Standard clinical knowledge regarding [mechanism] OR quote."
  }

**CRITICAL:**
If two entities exist in the text, and there is ANY widely known medical reason to pause before combining them, LIST IT.
"""

# Make sure OPENAI_API_KEY is set in your environment
client = OpenAI()

# PDF -> plain text
def pdf_to_text(pdf_path: str) -> str:
    """Extract text from a PDF file using pypdf."""
    reader = PdfReader(pdf_path)
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text)
    return "\n\n".join(pages)

# Call chat.completions and parse JSON
def extract_from_paper_text(paper_text: str) -> dict | None:
    """
    Single call:
      input: paper_text
      output: { "entities": [...], "relationships": [...], "interactions": [...] }
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",   # or "gpt-4o" if you want more power
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": paper_text},
        ],
        temperature=0.1,
    )

    output_text = response.choices[0].message.content.strip()

    # strip ```json or ``` fences if present
    if output_text.startswith("```json"):
        output_text = output_text[len("```json"):].strip()
    elif output_text.startswith("```"):
        output_text = output_text[len("```"):].strip()

    if output_text.endswith("```"):
        output_text = output_text[:-3].strip()

    try:
        validated_json = json.loads(output_text)
    except json.JSONDecodeError:
        print("LLM did not return valid JSON. Raw output:")
        print(output_text)
        validated_json = None

    return validated_json


def main():
    parser = argparse.ArgumentParser(
        description="Extract entities, relationships, and interactions from a medical PDF."
    )
    parser.add_argument("pdf_path", help="Path to the input PDF file.")
    parser.add_argument(
        "-o",
        "--output",
        help="Path to write JSON output (default: validated_interactions.json).",
        default="validated_interactions.json",
    )
    args = parser.parse_args()

    if not os.path.exists(args.pdf_path):
        raise FileNotFoundError(f"PDF not found: {args.pdf_path}")

    print(f"Reading PDF: {args.pdf_path}")
    paper_text = pdf_to_text(args.pdf_path)

    print("Calling OpenAI API to extract entities/relationships/interactions...")
    result = extract_from_paper_text(paper_text)

    if result is None:
        print("No valid JSON returned; nothing to save.")
        return

    json_str = json.dumps(result, indent=2, ensure_ascii=False)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(json_str)
        print(f"Wrote JSON to {args.output}")
    else:
        print(json_str)

if __name__ == "__main__":
    main()
