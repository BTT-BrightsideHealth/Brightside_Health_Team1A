
import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

from extract.prompt import EXTRACT_PROMPT

# load environment variable
load_dotenv()
genai.configure(api_key=os.getenv("GENAI_API_KEY"))

#read the two training txt files
file_paths = ["output_text.txt", "output2_text.txt"]
texts = []

for path in file_paths:
    with open(path, 'r', encoding='utf-8') as file:
        texts.append(file.read())

# split txt into chunks
def chunck_text(text, chunck_size=1000):
    words = text.split()
    chuncks = []
    for i in range(0, len(words), chunck_size):
        chuncks.append(' '.join(words[i:i + chunck_size]))
    return chuncks

#combine output
combined = {"entities": [], "relationships": []}
unique_entities = set()
unique_relationships = set()

model = genai.GenerativeModel("gemini-1.5-flash")


for i, text in enumerate(texts, 1):
    chuncks = chunck_text(text)
    for j, chunck in enumerate(chuncks, 1):

        full_prompt = f"""
        {EXTRACT_PROMPT}
        Text section {j} of file {i}:
        {chunck}
        Please respond with the JSON object containing all the extracted entities and relationships.
        """
        
        response = model.generate_content(full_prompt)

        cleaned_text = response.text.strip()
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[len("```json"):].strip()
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3].strip()


        try:
            data = json.loads(cleaned_text)
            
            # deduplicate entities
            for entity in data.get("entities", []):
                entity_key = (entity.get("id"), entity.get("name"), entity.get("type"))
                if entity_key not in unique_entities:
                    unique_entities.add(entity_key)
                    combined["entities"].append(entity)
            # deduplicate relationships
            for relationship in data.get("relationships", []):
                relationship_key = (relationship.get("head"), relationship.get("tail"), relationship.get("type"), relationship.get("evidence"))
                if relationship_key not in unique_relationships:
                    unique_relationships.add(relationship_key)
                    combined["relationships"].append(relationship)

                
        except json.JSONDecodeError:
            combined.setdefault("raw_responses", []).append(cleaned_text)

#save
with open("combined-final.json", "w", encoding="utf-8") as f:
    json.dump(combined, f, ensure_ascii=False, indent=2)

print("JSON output saved to combined-final.json")

