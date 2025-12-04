import pickle
import networkx as nx
import streamlit as st
from pyvis.network import Network
import os
import re

# Streamlit setup
st.set_page_config(page_title="Brightside Knowledge Graph", layout="wide")
st.title("Brightside Health Knowledge Graph Explorer")

# Load the saved graph (Edwin's data)
if not os.path.exists("graph.gpickle"):
    st.error(" graph.gpickle not found. Run build_graph_from_json.py first.")
    st.stop()

with open("graph.gpickle", "rb") as f:
    G = pickle.load(f)

# --- Sidebar controls ---
st.sidebar.header("Display Options")
limit = st.sidebar.slider("Show up to N nodes", 100, len(G), 300, step=50)
st.sidebar.write("(Use fewer nodes for faster rendering)")

# --- Search bar ---
query = st.text_input("🔎 Search for a keyword (e.g. sertraline, anxiety, depression):").strip().lower()

# --- Build subgraph ---
if len(G) > limit:
    nodes_subset = list(G.nodes())[:limit]
    subgraph = G.subgraph(nodes_subset)
else:
    subgraph = G

# --- Filter / highlight based on search ---
matched_nodes = []
if query:
    pattern = re.compile(query, re.IGNORECASE)
    matched_nodes = [
        n for n, data in subgraph.nodes(data=True)
        if pattern.search(str(data.get("label", ""))) or pattern.search(str(n))
    ]

# --- Build visualization ---
net = Network(height="800px", width="100%", bgcolor="#111", font_color="white", notebook=False)

for node, data in subgraph.nodes(data=True):
    node_type = data.get("type", "").lower()
    color = "#6AAFFF"  # default blue
    if "drug" in node_type:
        color = "#1f77b4"
    elif "condition" in node_type or "disease" in node_type:
        color = "#d62728"
    elif "symptom" in node_type:
        color = "#2ca02c"

    # Highlight matched nodes in yellow
    if node in matched_nodes:
        color = "#FFD700"

    net.add_node(node, label=data.get("label", node), color=color)

# Add edges
for src, dst, data in subgraph.edges(data=True):
    rel_type = data.get("type", "")
    net.add_edge(src, dst, title=rel_type)

# --- Save and embed the graph ---
net.save_graph("interactive_graph.html")

with open("interactive_graph.html", "r", encoding="utf-8") as f:
    html = f.read()

st.components.v1.html(html, height=850, scrolling=True)

# --- Display info ---
st.markdown(f"**Total Graph Size:** {G.number_of_nodes()} nodes, {G.number_of_edges()} edges.")
if query:
    if matched_nodes:
        st.success(f"Found {len(matched_nodes)} matches for '{query}' (highlighted in yellow).")
    else:
        st.warning(f"No matches found for '{query}'.")

