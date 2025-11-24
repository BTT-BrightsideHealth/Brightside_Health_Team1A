# Brightside_Health_Team1A


1. Copy `.env.example` → `.env`
2. Open `.env` and paste your real OpenAI key:
3. 3. Run `python test_env.py` to check the key is loaded


To run: `docker compose up --build -d neo4j`
To run Graph generator: `docker compose -f 'docker-compose.yml' up -d --build 'loader'`
Go to: http://localhost:7474/browser/
Run `docker compose down` to stop contianers from running
