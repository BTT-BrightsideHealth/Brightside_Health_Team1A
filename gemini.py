import os
import json
from dotenv import load_dotenv
from openai import OpenAI
import re  
from extract.prompt import EXTRACT_PROMPT


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# input files 
file_paths = ["output_text.txt", "output2_text.txt"]
texts = []
for path in file_paths:
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            texts.append(f.read())
    else:
        print(f"Warning: Input file not found: {path}. Skipping.")

# split text into fixed-size chunks 
def chunk_text(text, chunk_size=1000):
    words = text.split()
    return [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]

# canonical map for common acronyms and major synonyms.
# all keys and values must be run through normalize_text first for consistency
CANONICAL_MAP = {
    "ssris": "selective serotonin reuptake inhibitors",
    "tcasa": "tricyclic antidepressants",
    "vns": "vagus nerve stimulation",
    "dbs": "deep brain stimulation",
    "ect": "electroconvulsive therapy",
    "cbt": "cognitive behavioral therapy", # Simplified CBT
    "ip": "interpersonal therapy", # Assuming IP is Interpersonal Psychotherapy
    "maois": "monoamine oxidase inhibitors"
    }

# normalize text 
def normalize_text(s):
    if not isinstance(s, str):
        return ""
    
    s = s.strip().lower().replace("\n", " ")
    s = re.sub(r'\s*\([^)]*\)', '', s).strip()
    s = re.sub(r'[-\s]sr|[-\s]xr|sustained[-\s]release|extended[-\s]release', '', s)
    s = re.sub(r'quick\s+', '', s) 
    s = re.sub(r'self[-\s]report', '', s) 
    s = re.sub(r'rating\s+scale', 'scale', s) 
    s = re.sub(r'hamilton\s+depression\s+scale', 'hamilton depression', s)
    s = re.sub(r'\s+', ' ', s).strip()
    
    return s

# preprocess for deduplication 
def preprocess_entity(entity):
    raw_text = entity.get("text")
    entity_type = entity.get("type")
    normalized_text = normalize_text(raw_text)
    canonical_text = CANONICAL_MAP.get(normalized_text, normalized_text)
    
    return canonical_text, normalize_text(entity_type)

def preprocess_relationship(relationship):
    return (
        relationship.get("head"),
        relationship.get("tail"),
        normalize_text(relationship.get("type")),
        normalize_text(relationship.get("evidence"))
    )

# initialize canonicalization data 
entity_to_canonical_id = {}
canonical_entities = []
current_id = 1
combined_relationships = []

# process each file and chunk 
for i, text in enumerate(texts, 1):
    chunks = chunk_text(text)
    for j, chunk in enumerate(chunks, 1):
        full_prompt = f"""
    {EXTRACT_PROMPT}
    Text section {j} of file {i}:
    {chunk}

    Please respond ONLY with a valid JSON object containing all extracted entities and relationships.
    """

        print(f"Processing file {i}, chunk {j}/{len(chunks)} ...")

        try:
            # call ChatGPT (replace Gemini) 
            response = client.chat.completions.create(
                model="gpt-4o-mini",  
                messages=[{"role": "user", "content": full_prompt}],
                temperature=0.2,
            )

            cleaned_text = response.choices[0].message.content.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[len("```json"):].strip()
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3].strip()

            data = json.loads(cleaned_text)

            # canonicalize entities 
            local_id_to_key_map = {}
            for entity in data.get("entities", []):
                # use the new preprocessing function
                key = preprocess_entity(entity) 
                old_id = entity.get("id")
                if old_id is not None:
                    local_id_to_key_map[old_id] = key

                if key not in entity_to_canonical_id:
                    new_id = current_id
                    entity_to_canonical_id[key] = new_id
                    canonical_entities.append({
                        "id": new_id,
                        "text": entity["text"],
                        "type": entity["type"],
                        "code_system": entity.get("code_system"),
                        "code": entity.get("code")
                    })
                    current_id += 1

            # canonicalize relationships 
            for relationship in data.get("relationships", []):
                head_key = local_id_to_key_map.get(relationship.get("head"))
                tail_key = local_id_to_key_map.get(relationship.get("tail"))
                
                # check if keys exist before fetching canonical IDs
                if head_key and tail_key:
                    canonical_head_id = entity_to_canonical_id.get(head_key)
                    canonical_tail_id = entity_to_canonical_id.get(tail_key)
                else:
                    canonical_head_id, canonical_tail_id = None, None

                if canonical_head_id and canonical_tail_id:
                    combined_relationships.append({
                        "head": canonical_head_id,
                        "tail": canonical_tail_id,
                        "type": relationship.get("type"),
                        "evidence": normalize_text(relationship.get("evidence"))
                    })
                else:
                    print(f"Skipped relationship in file {i}, chunk {j}: missing entity mapping -> {relationship}")

        except json.JSONDecodeError as e:
            print(f"JSON Error in file {i}, chunk {j}: {e}. Content: {cleaned_text[:100]}...")
            continue
        except Exception as e:
            print(f"General Error in file {i}, chunk {j}: {e}")
            continue

# deduplicate relationships 
final_relationships = []
unique_relationships = set()
for r in combined_relationships:
    # Use a key that includes the evidence to preserve unique relationships with the same head/tail/type but different context
    key = (r['head'], r['tail'], r['type'], r['evidence']) 
    if key not in unique_relationships:
        unique_relationships.add(key)
        final_relationships.append(r)

# save final combined JSON 
final_combined = {
    "entities": canonical_entities,
    "relationships": final_relationships
}

with open("combined-final-CHATGPT.json", "w", encoding="utf-8") as f:
    json.dump(final_combined, f, ensure_ascii=False, indent=2)

print("FIXED JSON output saved to combined-final-CHATGPT.json")