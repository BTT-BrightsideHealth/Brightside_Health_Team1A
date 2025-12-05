# Brightside_Health_Team1A


1. Copy `.env.example` → `.env`
2. Open `.env` and paste your real OpenAI key:
3. 3. Run `python test_env.py` to check the key is loaded



### Overview
### What this does
This adds a simple Streamlit web app that lets you explore and search the Brightside Health Knowledge Graph.  
You can look up drugs, symptoms, or conditions and see how they’re connected in an interactive graph.

---

### How to run it locally
1. Make sure the file `combined-final-CHATGPT.json` is in the main project folder.  
2. Run this to build the graph:
   ```bash
   python build_graph_from_json.py
Install these dependencies:

bash
Copy code
pip install streamlit pyvis networkx
Start the app:

bash
Copy code: streamlit run search_graph_app.py
Open http://localhost:8501 in your browser.
To run: `docker compose up --build -d neo4j`
To run Graph generator: `docker compose -f 'docker-compose.yml' up -d --build 'loader'`
Go to: http://localhost:7474/browser/
Run `docker compose down` to stop contianers from running
