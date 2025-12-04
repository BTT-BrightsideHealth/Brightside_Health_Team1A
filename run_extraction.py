# run_extraction.py
import os
import json
import pdfplumber
from dotenv import load_dotenv
from openai import OpenAI
import networkx as nx
from extract.prompt_config import EXTRACTION_PROMPT

# 1.Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 2.CHANGE TO PDF FILE TO TEST 
PDF_PATH = "data/fava-et-al-2008-difference-in-treatment-outcome-in-outpatients-with-anxious-versus-nonanxious-depression-a-star_d-report.pdf"

def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:  # avoid None errors
                text += page_text + "\n"
    return text

#3.Read PDF text
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

# 5.Parse output
#raw_output = response.choices[0].message.content

#try:
#    data = json.loads(raw_output)
#    print(json.dumps(data, indent=2))
#except json.JSONDecodeError:
 #   print("⚠️ Model returned invalid JSON. Raw output:\n", raw_output)


# 5. Parse output and build knowledge graph
raw_output = response.choices[0].message.content

try:
    data = json.loads(raw_output)
    print("Parsed JSON from model")

    # Build a directed graph
    G = nx.DiGraph()

    # ----
    # NOTE: this is generic and should work if your JSON looks like either:
    # 1) {"entities": [...], "relations": [...]}
    # 2) a list of relation objects [{...}, {...}, ...]
    # You can tweak the key names later if needed.
    # ----

    if isinstance(data, dict) and "relations" in data:
        entities = data.get("entities", [])

        # Add entities as nodes
        for ent in entities:
            node_id = ent.get("id") or ent.get("name") or ent.get("label")
            if not node_id:
                continue
            # store everything else as node attributes
            attrs = {k: v for k, v in ent.items() if k not in ("id", "name", "label")}
            G.add_node(node_id, **attrs)

        # Add relations as edges
        for rel in data["relations"]:
            src = rel.get("source") or rel.get("from") or rel.get("drug")
            dst = rel.get("target") or rel.get("to") or rel.get("condition")
            label = rel.get("type") or rel.get("relation")
            if not (src and dst):
                continue
            G.add_node(src)
            G.add_node(dst)
            G.add_edge(src, dst, label=label)

    elif isinstance(data, list):
        # Assume each item is a relation-like object
        for rel in data:
            src = rel.get("source") or rel.get("from") or rel.get("drug")
            dst = rel.get("target") or rel.get("to") or rel.get("condition")
            label = rel.get("type") or rel.get("relation")
            if not (src and dst):
                continue
            G.add_node(src)
            G.add_node(dst)
            G.add_edge(src, dst, label=label)

    else:
        print("⚠️ JSON format unexpected; graph may be empty.")
        G = nx.DiGraph()

    # Save graph for Streamli

    import pickle
    with open("graph.gpickle", "wb") as f:
        pickle.dump(G, f) 
    print("Saved knowledge graph to graph.gpickle")

except json.JSONDecodeError:
    print("⚠️ Model returned invalid JSON. Raw output:\n", raw_output)
