# ===============================  
# 1. Load Environment Variables
# ===============================
import os
import requests
from dotenv import load_dotenv
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import chromadb
from supabase import create_client
from datetime import datetime, timedelta

# Ensure kaleido is installed
try:
    import kaleido
except ImportError:
    raise ImportError("⚠️ Please install kaleido: pip install kaleido")

os.makedirs("charts", exist_ok=True)
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY or not OPENROUTER_API_KEY:
    raise ValueError("⚠️ Please set SUPABASE_URL, SUPABASE_KEY, and OPENROUTER_API_KEY in .env")

# ===============================  
# 2. Connect to Supabase
# ===============================
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ===============================  
# 3. Schema Snapshot
# ===============================
SCHEMA = {
    "order_request": ["order_id", "orderpackageid", "ordersubjectid", "ordercompanycode",
                      "order_status", "order_packagecode", "order_request_time", "order_received_time"],
    "search_status": ["status_code", "status"],
    "search_type": ["search_type_code", "search_type", "search_type_category"],
    "subject": ["subject_id", "subject_name", "subject_alias", "subject_contact",
                "subject_address1", "subject_address2", "sbj_city"],
    "package": ["package_code", "package_name", "package_price", "comp_code"],
    "company": ["comp_id", "comp_name", "comp_code"]
}
TABLES = list(SCHEMA.keys())

# ===============================  
# 4. ChromaDB Setup
# ===============================
chroma_client = chromadb.PersistentClient(path="chroma_db")
collection = chroma_client.get_or_create_collection("schema_docs")

# ===============================  
# 5. Custom Embeddings
# ===============================
class CustomEmbedding:
    def embed_documents(self, texts):
        url = "http://localhost:11434/v1/embeddings"
        headers = {"Content-Type": "application/json"}
        data = {"model": "mxbai-embed-large:latest", "input": texts}
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return [d["embedding"] for d in response.json()["data"]]

    def embed_query(self, text):
        return self.embed_documents([text])[0]

embedding_model = CustomEmbedding()

def get_embedding(text: str):
    try:
        return embedding_model.embed_query(text)
    except Exception as e:
        print("⚠️ Failed to generate embedding:", e)
        return None

# ===============================  
# 6. Initialize Chroma DB
# ===============================
def init_chroma():
    if collection.count() == 0:
        docs, ids, embeds = [], [], []
        for table, cols in SCHEMA.items():
            for col in cols:
                doc = f"Table: {table}, Column: {col}"
                emb = get_embedding(doc)
                if emb:
                    docs.append(doc)
                    ids.append(f"{table}_{col}")
                    embeds.append(emb)
        if docs:
            collection.add(documents=docs, embeddings=embeds, ids=ids)
            print("✅ Chroma initialized with column-level embeddings")
        else:
            print("⚠️ No embeddings generated. Chroma DB not initialized")
    else:
        print("🔄 Using existing Chroma embeddings")

init_chroma()

# ===============================  
# 7. RAG Query Interpreter
# ===============================
def interpret_query_rag(user_query: str):
    query_emb = get_embedding(user_query)
    if query_emb is None:
        return {"table": None, "columns": []}
    
    results = collection.query(query_embeddings=[query_emb], n_results=3)
    matched_ids = results["ids"][0] if results["ids"] else []
    
    table_columns = []
    for id_str in matched_ids:
        if "_" in id_str:
            t, c = id_str.split("_", 1)
            table_columns.append((t, c))
    
    if not table_columns:
        return {"table": None, "columns": []}
    
    table_set = set([tc[0] for tc in table_columns])
    table = table_set.pop() if len(table_set) == 1 else table_columns[0][0]
    columns = [tc[1] for tc in table_columns]
    return {"table": table, "columns": columns}

# ===============================  
# 8. Fetch + Analyze Data
# ===============================
def fetch_and_answer(query: str):
    decision = interpret_query_rag(query)
    table, cols = decision.get("table"), decision.get("columns", [])
    
    if not table or table not in TABLES:
        print("🙏 Sorry, I can’t answer that request with the current database.")
        return
    
    response = supabase.table(table).select("*").limit(1000).execute()
    if not response.data:
        print(f"⚠️ No data in table {table}")
        return
    
    df = pd.DataFrame(response.data)
    query_lower = query.lower()
    
    # ===============================  
    # Handle counts
    # ===============================
    if "number of" in query_lower or "count" in query_lower:
        if "completed" in query_lower and "order_status" in df.columns:
            count_val = df[df["order_status"].str.lower() == "completed"].shape[0]
        elif "education verification" in query_lower and "subject_id" in df.columns:
            count_val = df.shape[0]
        else:
            count_val = len(df)
        print(f"\n💡 Answer:\nThere are {count_val} records")
        return
    
    # ===============================  
    # Handle unique values
    # ===============================
    if "unique" in query_lower:
        col = cols[0] if cols else df.columns[0]
        unique_vals = df[col].drop_duplicates().tolist()
        print(f"\n💡 Answer:\nUnique values in '{col}': {unique_vals}")
        return
    
    # ===============================  
    # Handle distributions
    # ===============================
    if "distribution" in query_lower:
        col = cols[0] if cols else df.columns[0]
        if pd.api.types.is_numeric_dtype(df[col]):
            plt.figure(figsize=(8,5))
            sns.histplot(df[col], kde=True, bins=20)
            plt.title(f"Distribution of {col}")
            path = f"charts/{table}_{col}_hist.png"
            plt.savefig(path, bbox_inches="tight")
            plt.close()
            print(f"\n💡 Answer:\nHistogram saved: {path}")
        else:
            plt.figure(figsize=(8,5))
            sns.countplot(y=df[col], order=df[col].value_counts().index)
            plt.title(f"Distribution of {col}")
            path = f"charts/{table}_{col}_dist.png"
            plt.savefig(path, bbox_inches="tight")
            plt.close()
            print(f"\n💡 Answer:\nDistribution chart saved: {path}")
        return
    
    # ===============================  
    # Handle time filters like "since yesterday"
    # ===============================
    if "since yesterday" in query_lower:
        time_cols = [c for c in df.columns if "time" in c]
        if time_cols:
            yesterday = datetime.now() - timedelta(days=1)
            df = df[pd.to_datetime(df[time_cols[0]]) >= yesterday]
            print(f"\n💡 Answer:\nRecords since yesterday: {df.shape[0]}")
        return
    
    # ===============================  
    # Default: show sample data
    # ===============================
    sample = df.head().to_dict(orient="records")
    print("\n💡 Answer:\nSample data:")
    for r in sample:
        print(r)

# ===============================  
# 9. Interactive Loop
# ===============================
if __name__ == "__main__":
    print("💡 Ask me questions about the database (type 'bye' to exit).")
    while True:
        user_query = input("\nEnter your query: ")
        if user_query.strip().lower() == "bye":
            print("👋 Goodbye!")
            break
        fetch_and_answer(user_query)
