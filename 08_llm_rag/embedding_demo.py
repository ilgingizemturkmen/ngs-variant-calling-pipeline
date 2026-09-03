from sentence_transformers import SentenceTransformer
import numpy as np

print("Embedding modeli yukleniyor (ilk calistirmada indirilecek)...")
model = SentenceTransformer('all-MiniLM-L6-v2')

cumleler = [
    "TP53 genindeki R175H mutasyonu kanserde sik gorulen bir hotspot mutasyondur.",
    "p53 proteinindeki 175. pozisyondaki degisim tumor baskilayici islevi bozar.",
    "BCR-ABL1 fuzyonu Kronik Miyeloid Losemi'nin klasik molekuler markeridir.",
    "Bugun hava cok guzeldi, parkta yuruyus yaptik."
]

print("\nCumleler embedding'e cevriliyor...")
embeddings = model.encode(cumleler)

print(f"\nHer cumle {embeddings.shape[1]} boyutlu bir vektore donustu.")

sorgu = "TP53 mutasyonu ne demek?"
sorgu_embedding = model.encode([sorgu])

benzerlikler = np.dot(embeddings, sorgu_embedding.T).flatten()

print(f"\nSorgu: '{sorgu}'")
print("\nEn benzer cumleler (benzerlik skoruna gore siralandi):")
sirali_indeksler = np.argsort(benzerlikler)[::-1]
for idx in sirali_indeksler:
    print(f"  [{benzerlikler[idx]:.3f}] {cumleler[idx]}")
