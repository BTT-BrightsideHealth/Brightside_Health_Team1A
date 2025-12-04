FROM python:3.13

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl tini && rm -rf /var/lib/apt/lists/*
    
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY . .

# Use tini as PID 1 for clean signals
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "generate_graph.py"]