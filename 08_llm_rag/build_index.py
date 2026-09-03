import os
import glob
import chromadb
from sentence_transformers import SentenceTransformer

print("Embedding modeli yukleniyor...")
model = SentenceTransformer('all-MiniLM-L6-v2')

print("README dosyalari toplaniyor...")
readme_paths = glob.glob("*/README.md")
print(f"Bulunan README sayisi: {len(readme_paths)}")
for p in readme_paths:
    print(f"  - {p}")

def chunk_text(text, chunk_size=500, overlap=50):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i+chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks

all_chunks = []
all_metadatas = []
all_ids = []
chunk_id = 0

for path in readme_paths:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    chunks = chunk_text(text)
    for chunk in chunks:
        all_chunks.append(chunk)
        all_metadatas.append({"source": path})
        all_ids.append(f"chunk_{chunk_id}")
        chunk_id += 1

print(f"\nToplam {len(all_chunks)} parca (chunk) olusturuldu.")

print("\nEmbedding'ler hesaplaniyor...")
embeddings = model.encode(all_chunks).tolist()

print("ChromaDB'ye kaydediliyor...")
client = chromadb.PersistentClient(path="08_llm_rag/chroma_db")
collection = client.get_or_create_collection(name="pipeline_docs")

collection.add(
    embeddings=embeddings,
    documents=all_chunks,
    metadatas=all_metadatas,
    ids=all_ids
)

print(f"\nBasarili: {len(all_chunks)} parca ChromaDB'ye kaydedildi.")
print("Veritabani konumu: 08_llm_rag/chroma_db")
