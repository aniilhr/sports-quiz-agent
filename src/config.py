import os
from dotenv import load_dotenv

# Load variables from .env file into the environment
load_dotenv()

# Centralized configuration values
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Path to the local JSON knowledge base
DATA_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "sports_facts.json")

# Path where ChromaDB will persist its vector store on disk
CHROMA_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "chroma_db")

if not GEMINI_API_KEY:
    print("[WARNING]: API Key is missing. Check your .env file setup!")