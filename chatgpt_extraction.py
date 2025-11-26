import os
import json
import argparse

from openai import OpenAI
from pypdf import PdfReader  # pip install pypdf

# System Prompt
SYSTEM_PROMPT = """
You are an information extraction system for medical research papers.

Given the text of a paper, you must return a SINGLE JSON object with exactly these top-level keys:
- "entities": list
- "relationships": list
- "interactions": list

=========================================================
1) ENTITIES
=========================================================
Each entity is:
  {
    "id": <int>,              // unique, incremental, starting at 1
    "text": <string>,         // surface form from the paper
    "type": <string>          // one of:
                              // "medical_condition", "medication",
                              // "treatment_type", "outcome", "measure",
                              // "patient_group", "study", "other"
  }

Examples of entity types:
- "major depressive disorder" -> "medical_condition"
- "sertraline"                -> "medication"
- "cognitive-behavioral therapy" -> "treatment_type"
- "remission", "relapse"     -> "outcome"
- "Hamilton Depression Rating Scale (HDRS)" -> "measure"
- "adolescents", "elderly", "pregnant patients" -> "patient_group"
- Named clinical trials or large studies -> "study"

=========================================================
2) RELATIONSHIPS
=========================================================
Each relationship is:
  {
    "head": <int>,            // entity id
    "tail": <int>,            // entity id
    "type": <string>,         // e.g. "treats", "has_outcome", "affects", "compares"
    "evidence": <string>      // quote or short paraphrase from the paper
  }

Examples:
- A medication that treats a condition: type = "treats"
- A treatment that leads to remission/relapse: type = "has_outcome"
- A patient group that changes efficacy/safety of a treatment: type = "affects"
- A study directly comparing two treatments: type = "compares"

All "head" and "tail" values must refer to valid entity IDs.

=========================================================
3) INTERACTIONS  (THIS IS IMPORTANT)
=========================================================
Now, using BOTH:
- the information from this paper, AND
- your general, widely taught medical and pharmacologic knowledge,

identify pairs of medications and/or somatic treatments from the "entities" list
that usually:
  - SHOULD NOT be taken together (contraindicated), or
  - SHOULD ONLY be used together with strong caution and close monitoring.

Work ONLY with entities that already appear in the "entities" array and whose type is
"medication" or "treatment_type".

Each interaction is:
  {
    "id": <int>,                      // unique, incremental, starting at 1
    "entity_ids": [<int>, <int>],     // EXACTLY TWO entity IDs from "entities"
    "interaction_type": <string>,     // "contraindicated" or "use_with_caution"
    "note": <string>,                 // short plain-language explanation
    "evidence": <string>              // brief mechanism / rationale or quote
  }

Details:
- "entity_ids":
    - Must contain exactly two IDs.
    - Each ID must match an existing entity "id" from the "entities" array.
- "interaction_type":
    - "contraindicated" if the combination is generally avoided / not recommended.
    - "use_with_caution" if the combo is possible but carries important risks
      (e.g. serotonin syndrome, additive sedation, QT prolongation, blood pressure
      changes) and typically needs monitoring or specialist oversight.
- "note":
    - 1–2 sentences in plain language, and it MUST clearly mention the TWO
      medications/treatments by name, e.g.:
      "Combining SSRIs and tricyclic antidepressants increases serotonergic effects
       and should be done only with specialist oversight."
- "evidence":
    - Either:
      - a short explanation of the known pharmacologic mechanism, OR
      - a relevant quote/paraphrase from the paper IF it explicitly mentions
        the interaction.

How many interactions:
- When there are multiple medications or somatic treatments in "entities",
  try to propose roughly 5–10 of the most clinically relevant pairs.
- Do NOT invent obscure or speculative interactions. Focus on commonly taught,
  clinically meaningful cautions and contraindications.
- If you truly cannot identify any important interactions between the listed
  entities, you may return:
  "interactions": []

=========================================================
4) GENERAL RULES
=========================================================
- All "head", "tail", and "entity_ids" values must refer to valid "id" values in "entities".
- Entity IDs in "entities" should be sequential starting from 1.
- Use verbatim names from the paper for "text" where possible.
- This JSON is for RESEARCH AND EDUCATIONAL purposes only and MUST NOT be used
  for real clinical or treatment decisions.

Return ONLY the JSON object. Do not include any extra text before or after it.
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
