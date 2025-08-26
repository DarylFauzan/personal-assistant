import os
from dotenv import load_dotenv

load_dotenv()

import pandas as pd
from sqlalchemy import create_engine, text
from langchain_ollama import OllamaEmbeddings

def fetch_cv(question: str):
    embedding_model = OllamaEmbeddings(model="qwen3:14b")
    emb = embedding_model.embed_query(question)
    db_username = os.getenv("DB_USERNAME")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")
    
    url = f"postgresql+psycopg2://{db_username}:{db_password}@{db_host}:{port}/{db_name}"
    
    engine = create_engine(url)
    
    print("📄fetching documents...")

    query = text(f"""
    select * 
    from qwen3_14b_chunks
    order by embeddings <=> array{emb}::vector
    limit 3;
    """)

    print("fetching document success")
    
    dfx = pd.read_sql_query(query,con=engine)

    documents = ""
    for index, row in dfx.iterrows():
        documents += f"{row['chunks']}\n{row['file_name']}\n\n================================="

    return documents