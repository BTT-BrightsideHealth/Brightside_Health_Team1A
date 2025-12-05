import streamlit as st
import json
from pyvis.network import Network
import tempfile
import os
from typing import Dict, List, Optional
from neo4j import GraphDatabase

# Page configuration
st.set_page_config(
    page_title="Knowledge Graph Visualization",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Color palette - easy on eyes but distinct
COLORS = {
    "primary": {
        "indigo_600": "#4f46e5",
        "indigo_700": "#4338ca",
        "indigo_900": "#312e81"
    },
    "background": {
        "gradient_from": "#eff6ff",
        "gradient_to": "#e0e7ff",
        "white": "#ffffff",
        "gray_50": "#f9fafb"
    },
    "text": {
        "primary": "#1f2937",
        "secondary": "#4b5563",
        "muted": "#6b7280",
        "white": "#ffffff"
    },
    "node_type": {
        "medical_condition": {"fill": "#3b82f6", "stroke": "#2563eb", "badge": "#dbeafe", "badge_text": "#1e40af"},  # Blue
        "medication": {"fill": "#10b981", "stroke": "#059669", "badge": "#d1fae5", "badge_text": "#047857"},  # Green
        "treatment_type": {"fill": "#8b5cf6", "stroke": "#7c3aed", "badge": "#ede9fe", "badge_text": "#6d28d9"},  # Purple
        "outcome": {"fill": "#f59e0b", "stroke": "#d97706", "badge": "#fef3c7", "badge_text": "#b45309"},  # Amber
        "measure": {"fill": "#ec4899", "stroke": "#db2777", "badge": "#fce7f3", "badge_text": "#be185d"},  # Pink
        "patient_group": {"fill": "#14b8a6", "stroke": "#0d9488", "badge": "#ccfbf1", "badge_text": "#0f766e"},  # Teal
        "study": {"fill": "#6366f1", "stroke": "#4f46e5", "badge": "#e0e7ff", "badge_text": "#4338ca"}  # Indigo
    },
    "graph": {
        "edge_line": "#cbd5e1",
        "edge_label": "#64748b",
        "selected_highlight": "#fbbf24",
        "border": "#e5e7eb"
    }
}

# Sample data from specifications
SAMPLE_DATA = {
    "nodes": [
        {"id": "1", "label": "Deep Learning", "type": "main"},
        {"id": "2", "label": "Medical Imaging", "type": "concept"},
        {"id": "3", "label": "CNN", "type": "method"},
        {"id": "4", "label": "Lung Cancer Detection", "type": "main"},
        {"id": "5", "label": "ResNet-50", "type": "method"},
        {"id": "6", "label": "CT Scans", "type": "concept"},
        {"id": "7", "label": "94% Accuracy", "type": "finding"},
        {"id": "8", "label": "Malignant Nodules", "type": "concept"},
        {"id": "9", "label": "Data Augmentation", "type": "method"},
        {"id": "10", "label": "Radiologist Support", "type": "finding"}
    ],
    "edges": [
        {"from": "1", "to": "2", "label": "applies to"},
        {"from": "1", "to": "3", "label": "uses"},
        {"from": "4", "to": "1", "label": "enabled by"},
        {"from": "3", "to": "5", "label": "implemented as"},
        {"from": "2", "to": "6", "label": "includes"},
        {"from": "1", "to": "7", "label": "achieves"},
        {"from": "6", "to": "8", "label": "identifies"},
        {"from": "5", "to": "9", "label": "enhanced by"},
        {"from": "7", "to": "10", "label": "enables"}
    ]
}

# Neo4j connection configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "test1234")

# Node types - use actual Neo4j types directly
NODE_TYPES = ["medical_condition", "medication", "treatment_type", "outcome", "measure", "patient_group", "study"]

@st.cache_resource
def get_neo4j_driver():
    """Get Neo4j driver connection (cached)."""
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=None)
        # Test connection
        with driver.session() as session:
            session.run("RETURN 1")
        return driver
    except Exception as e:
        st.error(f"Failed to connect to Neo4j: {str(e)}")
        return None

def fetch_nodes_from_neo4j(_driver) -> List[Dict]:
    """Fetch all nodes from Neo4j database."""
    nodes = []
    try:
        with _driver.session() as session:
            # Get all nodes with their labels and properties
            result = session.run("""
                MATCH (n)
                RETURN labels(n) as labels, properties(n) as props, id(n) as internal_id
            """)
            
            seen_ids = set()
            for record in result:
                labels = record["labels"]
                props = record["props"]
                internal_id = record["internal_id"]
                
                # Get the primary label (first label)
                node_label = labels[0] if labels else "Unknown"
                
                # Get node ID (prefer 'id' property, fallback to text, then internal Neo4j id)
                node_id = props.get("id")
                if node_id is None:
                    node_id = props.get("text")
                if node_id is None:
                    node_id = str(internal_id)
                
                node_id = str(node_id)
                
                # Skip duplicates (in case same node appears multiple times)
                if node_id in seen_ids:
                    continue
                seen_ids.add(node_id)
                
                # Get text/label for display
                node_text = props.get("text", props.get("name", f"Node {node_id}"))
                
                # Use Neo4j label directly as type (must be one of our defined types)
                # If not in our list, default to medical_condition
                if node_label not in NODE_TYPES:
                    node_label = "medical_condition"
                
                nodes.append({
                    "id": node_id,
                    "label": node_text,
                    "type": node_label,  # Use actual Neo4j type
                    "neo4j_label": node_label,
                    "properties": props
                })
    except Exception as e:
        st.error(f"Error fetching nodes: {str(e)}")
    
    return nodes

def fetch_edges_from_neo4j(_driver) -> List[Dict]:
    """Fetch all relationships from Neo4j database."""
    edges = []
    try:
        with _driver.session() as session:
            # Get all relationships
            # Try to match by id first, then text, then internal id
            result = session.run("""
                MATCH (a)-[r]->(b)
                RETURN 
                    coalesce(toString(a.id), toString(a.text), toString(id(a))) as from_id,
                    coalesce(toString(b.id), toString(b.text), toString(id(b))) as to_id,
                    type(r) as rel_type,
                    properties(r) as rel_props
            """)
            
            for record in result:
                from_id = str(record["from_id"])
                to_id = str(record["to_id"])
                rel_type = record["rel_type"]
                rel_props = record["rel_props"] or {}
                
                # Get relationship label (use type, or note/evidence if available)
                rel_label = rel_type.lower().replace("_", " ")
                if rel_props.get("note"):
                    rel_label = rel_props["note"]
                elif rel_props.get("evidence"):
                    # Use first line of evidence if it's short
                    evidence = rel_props["evidence"]
                    if isinstance(evidence, str) and len(evidence) < 50:
                        rel_label = evidence
                
                edges.append({
                    "from": from_id,
                    "to": to_id,
                    "label": rel_label,
                    "type": rel_type,
                    "properties": rel_props
                })
    except Exception as e:
        st.error(f"Error fetching edges: {str(e)}")
    
    return edges

def fetch_graph_data_from_neo4j(_driver) -> Dict:
    """Fetch complete graph data from Neo4j."""
    nodes = fetch_nodes_from_neo4j(_driver)
    edges = fetch_edges_from_neo4j(_driver)
    
    return {
        "nodes": nodes,
        "edges": edges
    }

def fetch_subgraph_from_neo4j(_driver, node_id: str) -> Dict:
    """Fetch subgraph containing a specific node and all its connected nodes."""
    nodes = []
    edges = []
    node_ids_in_subgraph = set()
    
    try:
        with _driver.session() as session:
            # First, find the node by id or text
            # Try to match by id property first, then by text, then by internal id
            result = session.run("""
            MATCH (n)
            WHERE coalesce(toString(n.id), toString(n.text), toString(id(n))) = $node_id
            RETURN labels(n) as labels, properties(n) as props, id(n) as internal_id
            LIMIT 1
        """, node_id=node_id)
            
            start_node = None
            for record in result:
                labels = record["labels"]
                props = record["props"]
                internal_id = record["internal_id"]
                
                node_label = labels[0] if labels else "Unknown"
                if node_label not in NODE_TYPES:
                    node_label = "medical_condition"
                
                # Get node ID
                nid = props.get("id")
                if nid is None:
                    nid = props.get("text")
                if nid is None:
                    nid = str(internal_id)
                nid = str(nid)
                
                node_text = props.get("text", props.get("name", f"Node {nid}"))
                
                start_node = {
                    "id": nid,
                    "label": node_text,
                    "type": node_label,
                    "neo4j_label": node_label,
                    "properties": props
                }
                node_ids_in_subgraph.add(nid)
                nodes.append(start_node)
                break
            
            if not start_node:
                return {"nodes": [], "edges": []}
            
            # Now find all nodes connected to this node (incoming and outgoing relationships)
            # Get all relationships where this node is involved
            rel_result = session.run("""
                MATCH (a)-[r]->(b)
                WHERE coalesce(toString(a.id), toString(a.text), toString(id(a))) = $node_id
                OR coalesce(toString(b.id), toString(b.text), toString(id(b))) = $node_id
                RETURN 
                    coalesce(toString(a.id), toString(a.text), toString(id(a))) as from_id,
                    coalesce(toString(b.id), toString(b.text), toString(id(b))) as to_id,
                    type(r) as rel_type,
                    properties(r) as rel_props,
                    labels(a) as from_labels,
                    labels(b) as to_labels,
                    properties(a) as from_props,
                    properties(b) as to_props,
                    id(a) as from_internal_id,
                    id(b) as to_internal_id
            """, node_id=node_id)
            
            for record in rel_result:
                from_id = str(record["from_id"])
                to_id = str(record["to_id"])
                rel_type = record["rel_type"]
                rel_props = record["rel_props"] or {}
                
                # Add from node if not already added
                if from_id not in node_ids_in_subgraph:
                    from_labels = record["from_labels"]
                    from_props = record["from_props"]
                    from_internal_id = record["from_internal_id"]
                    
                    from_label = from_labels[0] if from_labels else "Unknown"
                    if from_label not in NODE_TYPES:
                        from_label = "medical_condition"
                    
                    from_text = from_props.get("text", from_props.get("name", f"Node {from_id}"))
                    
                    nodes.append({
                        "id": from_id,
                        "label": from_text,
                        "type": from_label,
                        "neo4j_label": from_label,
                        "properties": from_props
                    })
                    node_ids_in_subgraph.add(from_id)
                
                # Add to node if not already added
                if to_id not in node_ids_in_subgraph:
                    to_labels = record["to_labels"]
                    to_props = record["to_props"]
                    to_internal_id = record["to_internal_id"]
                    
                    to_label = to_labels[0] if to_labels else "Unknown"
                    if to_label not in NODE_TYPES:
                        to_label = "medical_condition"
                    
                    to_text = to_props.get("text", to_props.get("name", f"Node {to_id}"))
                    
                    nodes.append({
                        "id": to_id,
                        "label": to_text,
                        "type": to_label,
                        "neo4j_label": to_label,
                        "properties": to_props
                    })
                    node_ids_in_subgraph.add(to_id)
                
                # Add edge
                rel_label = rel_type.lower().replace("_", " ")
                if rel_props.get("note"):
                    rel_label = rel_props["note"]
                elif rel_props.get("evidence"):
                    evidence = rel_props["evidence"]
                    if isinstance(evidence, str) and len(evidence) < 50:
                        rel_label = evidence
                
                edges.append({
                    "from": from_id,
                    "to": to_id,
                    "label": rel_label,
                    "type": rel_type,
                    "properties": rel_props
                })
            
    except Exception as e:
        st.error(f"Error fetching subgraph: {str(e)}")
    
    return {
        "nodes": nodes,
        "edges": edges
    }

def get_node_color(node_type: str) -> Dict[str, str]:
    """Get color configuration for a node type."""
    # Use the node type directly, fallback to medical_condition if not found
    return COLORS["node_type"].get(node_type, COLORS["node_type"]["medical_condition"])

def create_graph_network(nodes: List[Dict], edges: List[Dict], selected_node_id: Optional[str] = None) -> Network:
    """Create a pyvis network from nodes and edges."""
    net = Network(
        height="600px",  # Increased height
        width="100%",
        bgcolor=COLORS["background"]["white"],
        font_color=COLORS["text"]["primary"],
        directed=True
    )
    
    # Configure physics for circular-like layout
    net.set_options("""
    {
      "physics": {
        "enabled": true,
        "stabilization": {"enabled": true, "iterations": 200},
        "barnesHut": {
          "gravitationalConstant": -2000,
          "centralGravity": 0.1,
          "springLength": 200,
          "springConstant": 0.04,
          "damping": 0.09
        }
      },
      "nodes": {
        "font": {"size": 12, "color": "#ffffff"},
        "borderWidth": 2,
        "shadow": true
      },
      "edges": {
        "color": {"color": "#cbd5e1"},
        "font": {"size": 11, "color": "#64748b", "align": "middle"},
        "arrows": {"to": {"enabled": true, "scaleFactor": 0.5}},
        "smooth": {"type": "continuous"}
      }
    }
    """)
    
    # Add nodes
    for node in nodes:
        node_id = str(node["id"])
        node_type = node.get("type", "concept")
        colors = get_node_color(node_type)
        
        # Determine if node is selected
        is_selected = selected_node_id == node_id
        border_color = COLORS["graph"]["selected_highlight"] if is_selected else colors["stroke"]
        border_width = 4 if is_selected else 2
        
        # Split label for better display (max 2 words per line)
        label_parts = node["label"].split()
        if len(label_parts) > 2:
            label = " ".join(label_parts[:2]) + "\n" + " ".join(label_parts[2:])
        else:
            label = node["label"]
        
        net.add_node(
            node_id,
            label=label,
            color=colors["fill"],
            borderWidth=border_width,
            borderWidthSelected=border_width,
            font={"color": COLORS["text"]["white"], "size": 12},
            size=35 if is_selected else 30,
            title=f"{node['label']} ({node_type})"
        )
    
    # Add edges
    for edge in edges:
        net.add_edge(
            str(edge["from"]),
            str(edge["to"]),
            label=edge.get("label", ""),
            color=COLORS["graph"]["edge_line"],
            font={"color": COLORS["graph"]["edge_label"], "size": 11}
        )
    
    return net

def render_custom_css():
    """Render custom CSS for styling."""
    st.markdown("""
    <style>
        /* Global background */
        html, body, .main, .stApp, .block-container {
            background-color: #eff6ff !important;
            background: #eff6ff !important;
        }
        
        /* Header styling */
        .header-container {
            text-align: center;
            margin-bottom: 3rem;
        }
        
        .header-title {
            font-size: 2rem;
            font-weight: 500;
            color: #312e81;
            margin-bottom: 0.5rem;
        }
        
        .header-description {
            font-size: 1rem;
            color: #4b5563;
        }
        
        /* Card styling */
        .card {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 0.5rem;
            padding: 1.5rem;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        }
        
        .card-title {
            font-size: 1.25rem;
            font-weight: 500;
            color: #1f2937;
            margin-bottom: 0.5rem;
        }
        
        .card-description {
            font-size: 0.875rem;
            color: #6b7280;
            margin-bottom: 1rem;
        }
        
        /* Legend styling */
        .legend {
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            margin-top: 1rem;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .legend-indicator {
            width: 16px;
            height: 16px;
            border-radius: 9999px;
            border: 2px solid;
        }
        
        .legend-label {
            font-size: 0.875rem;
            color: #4b5563;
        }
        
        /* Details panel styling */
        .details-field {
            margin-bottom: 0.75rem;
        }
        
        .details-label {
            font-size: 0.875rem;
            font-weight: 500;
            color: #4b5563;
            margin-bottom: 0.25rem;
        }
        
        .details-value {
            font-size: 1rem;
            color: #1f2937;
        }
        
        .badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 0.25rem;
            font-size: 0.875rem;
            font-weight: 500;
        }
        
        .badge-medical_condition { background: #dbeafe; color: #1e40af; }
        .badge-medication { background: #d1fae5; color: #047857; }
        .badge-treatment_type { background: #ede9fe; color: #6d28d9; }
        .badge-outcome { background: #fef3c7; color: #b45309; }
        .badge-measure { background: #fce7f3; color: #be185d; }
        .badge-patient_group { background: #ccfbf1; color: #0f766e; }
        .badge-study { background: #e0e7ff; color: #4338ca; }
        
        /* Overlay details panel */
        .details-overlay {
            position: fixed;
            top: 120px;
            right: 20px;
            width: 350px;
            max-height: calc(100vh - 140px);
            overflow-y: auto;
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 0.5rem;
            padding: 1.5rem;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            z-index: 1000;
        }
        
        /* Search bar styling */
        .search-container {
            margin-bottom: 1rem;
        }
        
        .stTextInput > div > div > input {
            border-radius: 0.5rem;
            border: 1px solid #e5e7eb;
            padding: 0.5rem 1rem;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #4f46e5;
            box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
        }
        
        .connected-node {
            background: #f9fafb;
            color: #374151;
            padding: 0.5rem;
            border-radius: 0.25rem;
            margin-bottom: 0.25rem;
            font-size: 0.875rem;
        }
        
        .empty-state {
            color: #6b7280;
            font-style: italic;
            text-align: center;
            padding: 2rem;
        }
        
        /* Button styling */
        .stButton > button {
            background-color: #4f46e5;
            color: white;
            border-radius: 0.5rem;
            padding: 0.5rem 1rem;
            font-weight: 500;
            border: none;
        }
        
        .stButton > button:hover {
            background-color: #4338ca;
        }
        
        /* Hide Streamlit default elements */
        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }
        header { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

def get_node_details(node_id: str, nodes: List[Dict], edges: List[Dict]) -> Optional[Dict]:
    """Get details for a specific node including connected nodes."""
    node = next((n for n in nodes if str(n["id"]) == node_id), None)
    if not node:
        return None
    
    # Find connected nodes
    connected = []
    for edge in edges:
        if str(edge["from"]) == node_id:
            connected_node = next((n for n in nodes if str(n["id"]) == edge["to"]), None)
            if connected_node:
                connected.append({
                    "node": connected_node,
                    "relationship": edge.get("label", ""),
                    "direction": "outgoing",
                    "rel_type": edge.get("type", "")
                })
        elif str(edge["to"]) == node_id:
            connected_node = next((n for n in nodes if str(n["id"]) == edge["from"]), None)
            if connected_node:
                connected.append({
                    "node": connected_node,
                    "relationship": edge.get("label", ""),
                    "direction": "incoming",
                    "rel_type": edge.get("type", "")
                })
    
    return {
        "node": node,
        "connected": connected
    }

def main():
    # Render custom CSS
    render_custom_css()
    
    # Initialize session state
    if "selected_node" not in st.session_state:
        st.session_state.selected_node = None
    
    # Get Neo4j connection
    driver = get_neo4j_driver()
    
    # Fetch graph data from Neo4j
    if driver:
        if "graph_data" not in st.session_state:
            with st.spinner("Loading graph data from Neo4j..."):
                st.session_state.graph_data = fetch_graph_data_from_neo4j(driver)
    else:
        # Fallback to sample data if Neo4j is not available
        if "graph_data" not in st.session_state:
            st.warning("Neo4j connection failed. Using sample data.")
            st.session_state.graph_data = SAMPLE_DATA
    
    # Header
    st.markdown("""
    <div class="header-container">
        <h1 class="header-title">Research Paper Knowledge Graph</h1>
        <p class="header-description">Extract key concepts and relationships from research papers</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Top bar with search and refresh button
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.markdown('<h2 style="color: #1f2937; font-weight: 500;">Knowledge Graph Visualization</h2>', unsafe_allow_html=True)
    with col2:
        # Search bar (placeholder for now)
        search_query = st.text_input(
            "Search nodes...",
            key="search_input",
            placeholder="Search by name or type...",
            label_visibility="collapsed"
        )
    with col3:
        if driver and st.button("Refresh Graph", use_container_width=True, key="refresh_btn"):
            with st.spinner("Refreshing graph data from Neo4j..."):
                st.session_state.graph_data = fetch_graph_data_from_neo4j(driver)
                st.session_state.selected_node = None
                st.rerun()
    
    # Main content area - full width graph
    # Node selector dropdown - use full graph data for options
    graph_data = st.session_state.graph_data
    node_options = ["None"] + [f"{node['label']} (ID: {node['id']})" for node in graph_data["nodes"]]
    node_ids = [None] + [str(node["id"]) for node in graph_data["nodes"]]
    
    selected_index = 0
    if st.session_state.selected_node:
        try:
            selected_index = node_ids.index(st.session_state.selected_node)
        except ValueError:
            selected_index = 0
    
    selected_label = st.selectbox(
        "Select a node to view details:",
        options=node_options,
        index=selected_index,
        key="node_selector",
        label_visibility="collapsed"
    )
    
    # Update selected node based on dropdown selection
    previous_selected = st.session_state.selected_node
    if selected_label != "None":
        selected_node_id = node_ids[node_options.index(selected_label)]
        st.session_state.selected_node = selected_node_id
    else:
        st.session_state.selected_node = None
    
    # Fetch filtered graph data if a node is selected
    is_filtered = False
    if st.session_state.selected_node and driver:
        # Check if we need to fetch subgraph (node changed or not in cache)
        cache_key = f"subgraph_{st.session_state.selected_node}"
        if cache_key not in st.session_state or previous_selected != st.session_state.selected_node:
            with st.spinner("Loading connected nodes..."):
                filtered_data = fetch_subgraph_from_neo4j(driver, st.session_state.selected_node)
                st.session_state[cache_key] = filtered_data
        else:
            filtered_data = st.session_state[cache_key]
        
        # Use filtered data for graph
        display_data = filtered_data
        is_filtered = True
    else:
        # Show full graph when no node is selected
        display_data = graph_data
        is_filtered = False
        # Clear subgraph cache when no node is selected
        keys_to_remove = [k for k in list(st.session_state.keys()) if isinstance(k, str) and k.startswith("subgraph_")]
        for k in keys_to_remove:
            del st.session_state[k]
    
    # Main graph card (render after determining if filtered)
    filter_indicator = ""
    if is_filtered:
        filter_indicator = '<p style="color: #059669; font-size: 0.875rem; margin-top: 0.5rem;"><strong>Showing filtered view:</strong> Selected node and its connected nodes only.</p>'
    
    st.markdown(f"""
    <div class="card">
        <h3 class="card-title">Knowledge Graph</h3>
        <p class="card-description">Click on nodes to view details. Hover to highlight.</p>
        {filter_indicator}
    </div>
    """, unsafe_allow_html=True)
    
    # Create and render graph with filtered or full data
    net = create_graph_network(
        display_data["nodes"],
        display_data["edges"],
        st.session_state.selected_node
    )
    
    # Save graph to temporary HTML file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w") as tmp_file:
        net.save_graph(tmp_file.name)
        html_string = open(tmp_file.name, "r", encoding="utf-8").read()
        os.unlink(tmp_file.name)
    
    # Inject JavaScript to make graph interactive and sync with selector
    click_script = """
    <script>
    (function() {
        // Make nodes clickable and update the graph visualization
        const script = document.createElement('script');
        script.textContent = `
            window.addEventListener('load', function() {
                setTimeout(function() {
                    const network = window.network;
                    if (network) {
                        network.on('click', function(params) {
                            if (params.nodes.length > 0) {
                                const nodeId = params.nodes[0];
                                // Highlight the clicked node
                                network.selectNodes([nodeId]);
                                // Store in sessionStorage for potential future use
                                sessionStorage.setItem('selectedNode', nodeId);
                            }
                        });
                    }
                }, 1000);
            });
        `;
        document.head.appendChild(script);
    })();
    </script>
    """
    
    st.components.v1.html(html_string + click_script, height=650)
    
    # Legend with all node types
    legend_items = []
    for node_type in NODE_TYPES:
        colors = COLORS["node_type"][node_type]
        type_label = node_type.replace("_", " ").title()
        legend_items.append(
            f'<div class="legend-item">'
            f'<div class="legend-indicator" '
            f'style="background-color: {colors["fill"]}; border-color: {colors["stroke"]};"></div>'
            f'<span class="legend-label">{type_label}</span>'
            f'</div>'
        )

    legend_html = f"""
    <div class="legend">
        {''.join(legend_items)}
    </div>
    """

    st.markdown(legend_html, unsafe_allow_html=True)
    
    # Details panel as overlay
    if st.session_state.selected_node:
        details = get_node_details(
            st.session_state.selected_node,
            graph_data["nodes"],
            graph_data["edges"]
        )
        
        if details:
            node = details["node"]
            node_type = node.get("type", "medical_condition")
            properties = node.get("properties", {})
            neo4j_label = node.get("neo4j_label", "Unknown")

            # Use central color config for badge
            node_colors = COLORS["node_type"].get(node_type, COLORS["node_type"]["medical_condition"])
            badge_style = f'background: {node_colors["badge"]}; color: {node_colors["badge_text"]};'

            # Start building HTML string with *no leading spaces before <div>*
            parts = []

            parts.append(
                '<div class="details-overlay">'
                '<h3 style="margin-top: 0; color: #1f2937; font-weight: 500; font-size: 1.25rem;">Node Details</h3>'
                '<div class="details-field">'
                '<div class="details-label">Label</div>'
                f'<div class="details-value">{node["label"]}</div>'
                '</div>'
                '<div class="details-field">'
                '<div class="details-label">Neo4j Type</div>'
                f'<div class="details-value" style="font-family: monospace; color: #6b7280;">{neo4j_label}</div>'
                '</div>'
                '<div class="details-field">'
                '<div class="details-label">Category</div>'
                f'<span class="badge" style="{badge_style}">{node_type.replace("_", " ").title()}</span>'
                '</div>'
            )

            # Additional Properties
            if properties:
                additional_props = {
                    k: v for k, v in properties.items()
                    if k not in ["id", "text", "name", "type", "level"] and v is not None
                }

                if additional_props:
                    parts.append(
                        '<div class="details-field">'
                        '<div class="details-label">Additional Properties</div>'
                        '</div>'
                    )

                    for key, value in additional_props.items():
                        if isinstance(value, str) and len(value) > 100:
                            value = value[:100] + "..."
                        parts.append(
                            '<div class="connected-node" style="margin-bottom: 0.5rem;">'
                            f'<strong>{key.replace("_", " ").title()}:</strong> {value}'
                            '</div>'
                        )

            # Connected Nodes
            if details["connected"]:
                parts.append(
                    f'<div class="details-field">'
                    f'<div class="details-label">Connected Nodes ({len(details["connected"])})</div>'
                    '</div>'
                )

                for conn in details["connected"]:
                    direction_arrow = "→" if conn["direction"] == "outgoing" else "←"
                    rel_type = conn.get("rel_type", "")
                    rel_label = conn.get("relationship", "")

                    rel_display = rel_label
                    if rel_type and rel_type != rel_label:
                        rel_display = f'{rel_type.lower().replace("_", " ")}: {rel_label}'

                    parts.append(
                        '<div class="connected-node">'
                        f'{conn["node"]["label"]} {direction_arrow} {rel_display}'
                        '</div>'
                    )

            # Close wrapper
            parts.append('</div>')

            details_html = "".join(parts)

            st.markdown(details_html, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

