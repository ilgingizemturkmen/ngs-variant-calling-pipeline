import chromadb
from sentence_transformers import SentenceTransformer
from anthropic import Anthropic

print("Embedding modeli yukleniyor...")
model = SentenceTransformer("all-MiniLM-L6-v2")

with open("08_llm_rag/fabrika_ornegi/ariza_cozum_kayitlari.md", "r", encoding="utf-8") as f:
    text = f.read()

def chunk_by_section(text):
    sections = text.split("### Sorun:")
    chunks = []
    for section in sections[1:]:
        chunk = "Sorun:" + section.strip()
        chunks.append(chunk)
    return chunks

chunks = chunk_by_section(text)
print(f"Toplam {len(chunks)} ariza/cozum kaydi bulundu.")

print("Embedding'ler hesaplaniyor...")
embeddings = model.encode(chunks).tolist()

client = chromadb.PersistentClient(path="08_llm_rag/chroma_db")
collection = client.get_or_create_collection(name="fabrika_ariza_cozum")

ids = [f"ariza_{i}" for i in range(len(chunks))]
collection.upsert(
    embeddings=embeddings,
    documents=chunks,
    ids=ids
)

print(f"Basarili: {len(chunks)} ariza/cozum kaydi ChromaDB'ye kaydedildi.\n")

anthropic_client = Anthropic()

def fabrika_rag_sor(soru, n_sonuc=2):
    soru_embedding = model.encode([soru]).tolist()
    sonuclar = collection.query(query_embeddings=soru_embedding, n_results=n_sonuc)
    bulunan = sonuclar["documents"][0]

    print(f"--- Bulunan {len(bulunan)} ilgili kayit ---")
    for i, kayit in enumerate(bulunan):
        ilk_satir = kayit.split(chr(10))[0]
        print(f"[{i+1}] {ilk_satir}")

    baglam = "\n\n".join(bulunan)

    prompt = f"""Sen bir fabrika kalite/bakim uzmanisin. Asagidaki ariza-cozum
kayitlarini kullanarak operatorun sorusuna pratik, uygulanabilir bir
cevap ver. Sadece verilen kayitlara dayan.

ARIZA-COZUM KAYITLARI:
{baglam}

OPERATOR SORUSU: {soru}

CEVAP:"""

    response = anthropic_client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text

if __name__ == "__main__":
    soru = "Boyali parcalarda pürüzlü bir yüzey görüyoruz, portakal kabuğu gibi. Ne yapmaliyiz?"
    print(f"\nSORU: {soru}\n")
    cevap = fabrika_rag_sor(soru)
    print("\n" + "=" * 60)
    print("CEVAP:")
    print("=" * 60)
    print(cevap)
