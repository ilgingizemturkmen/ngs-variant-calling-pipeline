import os
import chromadb
from sentence_transformers import SentenceTransformer
from anthropic import Anthropic

print("Embedding modeli yukleniyor...")
model = SentenceTransformer("all-MiniLM-L6-v2")

print("ChromaDB'ye baglaniliyor...")
client = chromadb.PersistentClient(path="08_llm_rag/chroma_db")
collection = client.get_collection(name="pipeline_docs")

anthropic_client = Anthropic()

def rag_sor(soru, n_sonuc=3):
    soru_embedding = model.encode([soru]).tolist()

    sonuclar = collection.query(
        query_embeddings=soru_embedding,
        n_results=n_sonuc
    )

    bulunan_parcalar = sonuclar["documents"][0]
    kaynaklar = [m["source"] for m in sonuclar["metadatas"][0]]

    print(f"\n--- Bulunan {len(bulunan_parcalar)} ilgili parca ---")
    for i, (parca, kaynak) in enumerate(zip(bulunan_parcalar, kaynaklar)):
        print(f"[{i+1}] Kaynak: {kaynak}")
        print(f"    {parca[:150]}...\n")

    baglam = "\n\n".join(bulunan_parcalar)

    prompt = f"""Asagidaki dokuman parcalarini kullanarak soruyu yanitla.
Sadece verilen bilgiye dayanarak cevap ver, bilmiyorsan bilmedigini soyle.

DOKUMAN PARCALARI:
{baglam}

SORU: {soru}

CEVAP:"""

    print("--- Claude'a soruluyor ---\n")
    response = anthropic_client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text

if __name__ == "__main__":
    soru = "TP53 R175H mutasyonu nasil tespit edildi ve hangi araclarla dogrulandi?"
    cevap = rag_sor(soru)
    print("=" * 60)
    print("CEVAP:")
    print("=" * 60)
    print(cevap)
