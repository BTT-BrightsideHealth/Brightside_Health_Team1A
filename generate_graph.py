import json
from neo4j import GraphDatabase

# --- Settings ---
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "test1234"  # Replace with your actual password

# --- Load JSON File ---
with open('./extract/combined-final-CHATGPT.json', 'r') as f:
    data = json.load(f)

entities = data["entities"]
relationships = data["relationships"]

# --- Neo4j Driver ---
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# --- Create Nodes ---
def insert_entities(tx, entities):
    for ent in entities:
        label = ent["type"]
        props = {k: v for k, v in ent.items() if k != "type"}
        prop_str = ', '.join([f'{k}: ${k}' for k in props])
        cypher = f"MERGE (n:{label} {{id: $id}}) SET n += {{{prop_str}}}"
        tx.run(cypher, **props)

# --- Create Relationships ---
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
        '''
        # Cypher for relationship
        cypher = (f"MATCH (a:{head_label} {{id: $head_id}}), (b:{tail_label} {{id: $tail_id}}) "
                  f"MERGE (a)-[r:{rel_type} {{evidence: $evidence}}]->(b)")
        tx.run(cypher, head_id=head_id, tail_id=tail_id, evidence=evidence)
        '''

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