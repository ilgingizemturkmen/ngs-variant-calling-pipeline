# Hafta 10: LLM & RAG (Chroma, Anthropic API)

## Ozet

Pipeline'in tum haftalik README dokumantasyonu uzerinde, gercek bir
RAG (Retrieval-Augmented Generation) sistemi kuruldu. Sistem, kullanicinin
sorusuna en alakali dokuman parcalarini bulup (retrieval), bu parcalari
Claude'a (Anthropic API) baglam olarak vererek dogru, kaynagina sadik
bir cevap urettiriyor (generation).

## Ogrenilen Temel Kavramlar

- **Embedding**: Metni anlamsal benzerlik yakalayan sayisal vektore
  cevirme (sentence-transformers, all-MiniLM-L6-v2 modeli, 384 boyut)
- **Vector Database**: Embedding'leri saklayip hizli benzerlik aramasi
  yapan veritabani (ChromaDB, persistent/kalici modda)
- **Chunking**: Uzun dokumanlari kucuk, ortusen parcalara bolme
  (500 kelime, 50 kelime overlap)
- **Retrieval + Generation**: Soruyu embedding'e cevirip en yakin
  parcalari bul, bu parcalari LLM'e (Claude) baglam olarak ver

## Kurulum

```bash
pip3 install chromadb sentence-transformers anthropic --break-system-packages
```

Anthropic API anahtari console.anthropic.com uzerinden olusturuldu,
$5 kredi ile test edildi.

## Pipeline

1. `embedding_demo.py` - Temel embedding/benzerlik kavramini basit
   4 cumlelik ornekle gosterme
2. `build_index.py` - Tum hafta README'lerini (9 dosya) topla, parcala,
   embedding'e cevir, ChromaDB'ye kaydet (12 parca)
3. `rag_query.py` - Soru sor, en alakali 3 parcayi bul, Claude
   (claude-sonnet-4-5) ile baglam-sinirli cevap uret

## Test Sorgusu ve Sonuc

Soru: "TP53 R175H mutasyonu nasil tespit edildi ve hangi araclarla
dogrulandi?"

Claude, sadece verilen dokuman parcalarina dayanarak cevap uretti ve
onemli bir durustluk davranisi gosterdi: Hafta 5 README'si (IGV/VarDict
capraz dogrulamasinin detayli anlatildigi dosya) arama sonuclarinda
bulunmadigi icin, Claude "dogrulama icin kullanilan spesifik araclar
acikca yazilmamis" diyerek eksik bilgiyi ACIKCA belirtti - halusinasyon
yapip kendi bilgisinden (egitim verisinden) TP53 hakkinda bilgi
uydurmadi.

## Onemli Guvenlik Notu

Calisma sirasinda bir API anahtari yanlislikla bir sohbet arayuzune
yapistirilmis, hemen iptal edilip (revoke) yenisi olusturulmustur.
Ogrenilen ders: API anahtarlari SADECE terminal/kod icinde kullanilmali,
hicbir sohbet/log ortamina yazilmamalidir - sifreyle ayni hassasiyette
ele alinmalidir.

## Ogrenilen Ders

RAG'in en degerli ozelligi, LLM'in kendi (potansiyel yanlis/eskimis)
bilgisini kullanmak yerine, verilen guncel/dogru kaynaklarla sinirli
kalmasidir. Bu, kurumsal ortamlarda (ornegin sirket ic dokumantasyonu
uzerinde calisan bir chatbot) LLM halusinasyonunu onlemenin standart
yontemidir. Retrieval kalitesi (dogru parcalarin bulunmasi) dogrudan
generation kalitesini etkiler - bir parca bulunamazsa, LLM o konuda
"bilmiyorum" demeli, uydurmamalidir (ve bu ornekte tam olarak boyle
davrandi).

## Dosyalar

- embedding_demo.py - Temel embedding kavrami ornegi
- build_index.py - ChromaDB index olusturma scripti
- rag_query.py - RAG sorgu scripti
- chroma_db/ - Kalici vektor veritabani (gitignore'a eklenmeli)
