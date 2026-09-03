import chromadb
from sentence_transformers import SentenceTransformer
from anthropic import Anthropic

print("Embedding modeli yukleniyor...")
model = SentenceTransformer("all-MiniLM-L6-v2")

with open("08_llm_rag/ceo_ornegi/karar_destek_kayitlari.md", "r", encoding="utf-8") as f:
    text = f.read()

def chunk_by_section(text):
    sections = text.split("### Sorun:")
    chunks = []
    for section in sections[1:]:
        chunk = "Sorun:" + section.strip()
        chunks.append(chunk)
    return chunks

chunks = chunk_by_section(text)
print(f"Toplam {len(chunks)} karar destek kaydi bulundu.")

print("Embedding'ler hesaplaniyor...")
embeddings = model.encode(chunks).tolist()

client = chromadb.PersistentClient(path="08_llm_rag/chroma_db")
collection = client.get_or_create_collection(name="ceo_karar_destek")

ids = [f"karar_{i}" for i in range(len(chunks))]
collection.upsert(
    embeddings=embeddings,
    documents=chunks,
    ids=ids
)

print(f"Basarili: {len(chunks)} karar destek kaydi ChromaDB'ye kaydedildi.\n")

anthropic_client = Anthropic()

def ceo_rag_sor(soru, n_sonuc=2):
    soru_embedding = model.encode([soru]).tolist()
    sonuclar = collection.query(query_embeddings=soru_embedding, n_results=n_sonuc)
    bulunan = sonuclar["documents"][0]

    print(f"--- Bulunan {len(bulunan)} ilgili kayit ---")
    for i, kayit in enumerate(bulunan):
        ilk_satir = kayit.split(chr(10))[0]
        print(f"[{i+1}] {ilk_satir}")

    baglam = "\n\n".join(bulunan)

    prompt = f"""Sen deneyimli bir is danismanisin (yonetim danismanligi).
Asagidaki karar destek kayitlarini kullanarak CEO'nun sorusuna stratejik,
uygulanabilir bir tavsiye ver. Sadece verilen kayitlara dayan, gerekirse
onceliklendirme yap.

KARAR DESTEK KAYITLARI:
{baglam}

CEO SORUSU: {soru}

TAVSIYE:"""

    response = anthropic_client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text

if __name__ == "__main__":
    soru = "Ihracat yaptigimiz Avrupa pazarinda kur dalgalanmasi kar marjimizi eritiyor, ne yapmaliyiz?"
    print(f"\nSORU: {soru}\n")
    cevap = ceo_rag_sor(soru)
    print("\n" + "=" * 60)
    print("TAVSIYE:")
    print("=" * 60)
    print(cevap)
