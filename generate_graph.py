import os
import json
import re
from neo4j import GraphDatabase
from typing import Optional, Tuple

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
# Replace with actual password, match compose env
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "test1234") 

# Load JSON File
with open('./combined-final-CHATGPT.json', 'r') as f:
    data = json.load(f)

entities = data["entities"]
relationships = data["relationships"]

# load Neo4j Driver
driver = GraphDatabase.driver(NEO4J_URI, auth=None)  

# Create Entities
def insert_entities(tx, entities):
    for ent in entities:
        label = ent["type"]
        props = {k: v for k, v in ent.items() if k != "type"}

        cy_child = f"""
        MERGE (n:{label} {{id: $id}})
        SET n += $props,
            n.level = coalesce(n.level, 'child')
        """
        tx.run(cy_child, id=props["id"], props=props)

# Create Relationships
def insert_relationships(tx, relationships, entities):
    ent_dict = {e['id']: (e['type'], e['text']) for e in entities}
    for rel in relationships:
        head_id = rel["head"]
        tail_id = rel["tail"]
        rel_type = rel["type"].upper()
        evidence = rel.get("evidence", "")
        # Get labels for match
        head_label = ent_dict[head_id][0]
        tail_label = ent_dict[tail_id][0]

        cypher = f"""
        MATCH (a:{head_label} {{id: $head_id}}), (b:{tail_label} {{id: $tail_id}})
        MERGE (a)-[r:{rel_type}]->(b)
        // If relationship is new, set evidence to incoming value (may be empty)
        ON CREATE SET r.evidence = $evidence
        // If it exists, append only if this evidence isn't already present and isn't empty
        ON MATCH SET r.evidence =
            CASE
                WHEN $evidence = '' THEN r.evidence
                WHEN r.evidence IS NULL OR r.evidence = '' THEN $evidence
                WHEN r.evidence CONTAINS $evidence THEN r.evidence
                ELSE r.evidence + '\n' + $evidence
            END
        """
        tx.run(cypher, head_id=head_id, tail_id=tail_id, evidence=evidence)


def reset_graph(tx):
    tx.run("MATCH (n) DETACH DELETE n")  # Clear existing graph data
        

with driver.session() as session:
    session.execute_write(reset_graph)
    session.execute_write(insert_entities, entities)
    session.execute_write(insert_relationships, relationships, entities)

driver.close()
print("Graph successfully imported!")


'''
# Create high level rules manually for now
PARENT_RULES = [
    (re.compile(r'\bdepress', re.I), ("Depression", "group:depression")),
    (re.compile(r'\banx', re.I), ("Anxiety disorders", "group:anxiety")),
    (re.compile(r'\bbipolar', re.I), ("Bipolar disorder", "group:bipolar")),
    # add more rules as needed
]

# Takes in an entity, and sees tries to match with high level parent
def infer_parent(ent: dict) -> Tuple[Optional[str], Optional[str]]:
    """
    Returns (parent_name, parent_id) for an entity, or (None, None) if no parent.
    You can also drive this from ICD code prefixes, e.g., 'F33.*' -> Depression.
    """
    # only test with medical conditions for now
    if ent.get("type") != "medical_condition":
        return (None, None)

    text = (ent.get("text") or "").strip()
    if not text:
        return (None, None)

     Only implementing parent if we have time to implement later
    for pattern, (pname, pid) in PARENT_RULES:
        # Reverse string (Anxious depression) is a type of depression, not anxiety
        temp_list = text.split()
        temp_list.reverse()
        rev_text = " ".join(temp_list)

        if pattern.search(rev_text):
            return (pname, pid)

    return (None, None)
    

    # Create Nodes
def insert_entities(tx, entities):
    for ent in entities:
        label = ent["type"]
        props = {k: v for k, v in ent.items() if k != "type"}

        # 1) MERGE the child node (your existing behavior)
        #    We also tag child nodes with level='child' for clarity (optional).
        cy_child = f"""
        MERGE (n:{label} {{id: $id}})
        SET n += $props,
            n.level = coalesce(n.level, 'child')
        """
        tx.run(cy_child, id=props["id"], props=props)

        # 2) Infer parent group (name, id)
        parent_name, parent_id = infer_parent(ent)
        if not parent_name:
            continue

        # 3) MERGE the parent node (same label, distinct id), tag it as level='parent'
        cy_parent = f"""
        MERGE (p:{label} {{id: $parent_id}})
        ON CREATE SET p.name = $parent_name, p.level = 'parent'
        """
        tx.run(cy_parent, parent_id=parent_id, parent_name=parent_name)

        # 4) MERGE the relationship: (child)-[:IS_A]->(parent)
        cy_edge = f"""
        MATCH (n:{label} {{id: $id}}), (p:{label} {{id: $parent_id}})
        MERGE (n)-[:IS_A]->(p)
        """
        tx.run(cy_edge, id=props["id"], parent_id=parent_id)
        """
        prop_str = ', '.join([f'{k}: ${k}' for k in props])
        cypher = f"MERGE (n:{label} {{id: $id}}) SET n += {{{prop_str}}}"
        tx.run(cypher, **props)

'''