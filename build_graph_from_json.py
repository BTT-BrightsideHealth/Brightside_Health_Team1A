import json
import networkx as nx
import pickle

# 1️⃣ Load the combined JSON file that contains entities and relationships
with open("../combined-final-CHATGPT.json", "r") as f:

    data = json.load(f)

entities = data.get("entities", [])
relationships = data.get("relationships", [])

print(f"Loaded {len(entities)} entities and {len(relationships)} relationships")

# 2️⃣ Build a directed graph
G = nx.DiGraph()

# Add entities (nodes)
for ent in entities:
    node_id = ent.get("id")
    if not node_id:
        continue

    label = ent.get("text", node_id)
    node_type = ent.get("type", "Entity")

    # Add node with attributes
    G.add_node(node_id, label=label, type=node_type)

# Add relationships (edges)
for rel in relationships:
    head_id = rel.get("head")
    tail_id = rel.get("tail")
    rel_type = rel.get("type", "RELATION")
    evidence = rel.get("evidence", "")

    if not head_id or not tail_id:
        continue

    # Connect nodes with an edge
    G.add_edge(head_id, tail_id, type=rel_type, evidence=evidence)

# Print stats
print(f"Graph has {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")

# 3️⃣ Save the graph as a pickle file for Streamlit visualization
with open("graph.gpickle", "wb") as f:
    pickle.dump(G, f)

print(" Saved knowledge graph to graph.gpickle")

