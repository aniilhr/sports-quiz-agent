# --- Optional SQLite compatibility patch ---
# Some systems ship an outdated system sqlite3 that ChromaDB can't use.
# If you hit a sqlite version error, run: pip install pysqlite3-binary
# The try/except below auto-applies the fix only if that package is installed,
# so this file works whether or not you needed the patch.
try:
    __import__("pysqlite3")
    import sys
    sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
except ImportError:
    pass
# --------------------------------------------

import os
import json
import chromadb
from chromadb.utils import embedding_functions

from src.config import DATA_FILE_PATH, CHROMA_DB_PATH

COLLECTION_NAME = "sports_history"


def get_chroma_client():
    """Initializes and returns a persistent ChromaDB client saving to disk."""
    return chromadb.PersistentClient(path=CHROMA_DB_PATH)


def _get_collection(client):
    """Helper to fetch the shared collection with its embedding function."""
    embedding_fn = embedding_functions.DefaultEmbeddingFunction()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn
    )


def setup_and_populate_db(json_file_path=DATA_FILE_PATH):
    """
    Reads the offline JSON facts, creates a collection, and populates it.
    This only needs to run once, or when your local data changes.
    """
    client = get_chroma_client()
    collection = _get_collection(client)

    # Check if the database has already been populated
    if collection.count() > 0:
        print(f"Database already populated with {collection.count()} facts.")
        return collection

    # Check if data file exists
    if not os.path.exists(json_file_path):
        print(f"Error: Raw fact data file not found at {json_file_path}")
        return collection

    # Load and parse facts
    with open(json_file_path, "r") as f:
        facts_list = json.load(f)

    documents = []
    metadata_list = []
    ids = []

    for idx, item in enumerate(facts_list):
        documents.append(item["fact"])
        # Storing metadata allows us to filter queries by sport later!
        metadata_list.append({"sport": item["sport"]})
        ids.append(f"fact_{idx}")

    # Bulk add vectors to collection
    collection.add(
        documents=documents,
        metadatas=metadata_list,
        ids=ids
    )
    print(f"Successfully vectorized and stored {len(documents)} facts.")
    return collection


def query_historic_facts(sport, query_text, n_results=2):
    """
    Queries ChromaDB for historic documents relating to a sport.
    Filters database elements to match the selected sport category.
    """
    client = get_chroma_client()
    collection = _get_collection(client)

    # Query with metadata filtering so we only get facts for our target sport
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results,
        where={"sport": sport}
    )

    # Return matched documents list (or empty list if none found)
    return results.get("documents", [[]])[0]
