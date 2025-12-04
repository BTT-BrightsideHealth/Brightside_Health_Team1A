import streamlit as st
from pyvis.network import Network
import networkx as nx
import os

st.set_page_config(page_title="Brightside Knowledge Graph", layout="wide")
st.title(" Brightside Health Knowledge Graph")

if os.path.exists("graph.gpickle"):
    import pickle
    with open("graph.gpickle", "rb") as f:
        G = pickle.load(f)
else:
    G = nx.Graph()
    G.add_edge("Sertraline", "Depression")
    G.add_edge("Fluoxetine", "Anxiety")

net = Network(height="700px", width="100%", bgcolor="#111", font_color="white")
net.from_nx(G)
net.save_graph("graph.html")

with open("graph.html", "r", encoding="utf-8") as f:
    html = f.read()
st.components.v1.html(html, height=700, scrolling=True)

st.caption("Generated from research papers using GPT-4o extraction.")

