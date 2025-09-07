import os
from dotenv import load_dotenv

# load variables from .env
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
print("Loaded key starts with:", api_key[:10])  # only print first 10 chars

