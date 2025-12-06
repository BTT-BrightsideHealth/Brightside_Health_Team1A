# Brightside_Health_Team1A

## Local Development

1. Copy `.env.example` → `.env`
2. Open `.env` and paste your real OpenAI key:
3. Run `python test_env.py` to check the key is loaded

To run: `docker compose up --build -d neo4j`
To run Graph generator: `docker compose -f 'docker-compose.yml' up --build 'loader'`
Go to: http://localhost:7474/browser/
To run website: `docker-compose up streamlit`
Go to: http://0.0.0.0:8501
Run `docker compose down` to stop containers from running

## Streamlit Cloud Deployment

### Prerequisites

1. Set up a Neo4j database (Neo4j Aura DB or self-hosted)
2. Have your Neo4j connection details ready

### Deployment Steps

1. **Repository Setup**

   - Ensure `app.py` is at the repository root
   - Ensure `requirements.txt` is at the repository root (already configured)

2. **Configure Neo4j Connection**

   - In Streamlit Cloud: Go to your app → Settings → Secrets
   - Add the following secrets:
     ```
     NEO4J_URI = "bolt://your-neo4j-host:7687"
     NEO4J_USER = "your-username"  # Optional: leave empty if no auth
     NEO4J_PASSWORD = "your-password"  # Optional: leave empty if no auth
     ```
   - For Neo4j Aura DB, use the connection string provided (usually `neo4j+s://...`)
   - If your Neo4j instance doesn't require authentication, you can omit `NEO4J_USER` and `NEO4J_PASSWORD`

3. **Deploy**
   - Connect your GitHub repository to Streamlit Cloud
   - Streamlit Cloud will automatically detect `app.py` and deploy
   - The app will read Neo4j connection details from the secrets you configured

### Notes

- The app automatically handles both authenticated and unauthenticated Neo4j connections
- If `NEO4J_USER` is not set or empty, the app will connect without authentication
- Make sure your Neo4j instance is accessible from the internet (for Streamlit Cloud)
