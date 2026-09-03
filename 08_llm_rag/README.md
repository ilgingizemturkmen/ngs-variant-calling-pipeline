# Hafta 10: LLM & RAG (Chroma, Anthropic API)

## Ozet

Pipeline'in tum haftalik README dokumantasyonu uzerinde, gercek bir
RAG (Retrieval-Augmented Generation) sistemi kuruldu. Ayni mimari,
farkli alanlarda (biyoinformatik dokumantasyonu, fabrika ariza/cozum
kayitlari, CEO karar destek kayitlari) test edilerek RAG'in genel
amacli/tasinabilir dogasi gosterildi.

## Ogrenilen Temel Kavramlar

- **Embedding**: Metni anlamsal benzerlik yakalayan sayisal vektore
  cevirme (sentence-transformers, all-MiniLM-L6-v2 modeli, 384 boyut)
- **Vector Database**: Embedding'leri saklayip hizli benzerlik aramasi
  yapan veritabani (ChromaDB, persistent/kalici modda)
- **Chunking**: Uzun dokumanlari kucuk, anlamli parcalara bolme
- **Retrieval + Generation**: Soruyu embedding'e cevirip en yakin
  parcalari bul, bu parcalari LLM'e (Claude) baglam olarak ver

## Kurulum

```bash
pip3 install chromadb sentence-transformers anthropic --break-system-packages
```

Anthropic API anahtari console.anthropic.com uzerinden olusturuldu,
$5 kredi ile test edildi.

## Ornek 1: Pipeline Dokumantasyonu RAG

- `embedding_demo.py` - Temel embedding/benzerlik kavramini basit
  4 cumlelik ornekle gosterme
- `build_index.py` - Tum hafta README'lerini (9 dosya) topla, parcala,
  embedding'e cevir, ChromaDB'ye kaydet (12 parca)
- `rag_query.py` - Soru sor, en alakali 3 parcayi bul, Claude ile
  baglam-sinirli cevap uret

### Test Sonucu

Soru: "TP53 R175H mutasyonu nasil tespit edildi ve hangi araclarla
dogrulandi?"

Claude, onemli bir durustluk davranisi gosterdi: Hafta 5 README'si
(IGV/VarDict capraz dogrulamasinin detayli anlatildigi dosya) arama
sonuclarinda bulunmadigi icin, "dogrulama icin kullanilan spesifik
araclar acikca yazilmamis" diyerek eksik bilgiyi ACIKCA belirtti -
halusinasyon yapip kendi egitim verisinden bilgi uydurmadi.

## Ornek 2: Fabrika Ariza/Cozum RAG (fabrika_ornegi/)

Metal mobilya ayagi uretiminde tipik ariza/kalite sorunlarini
(kaynak hatalari, boya/kaplama sorunlari, boyutsal tolerans, makine
duruslari) iceren 8 kayitlik temsili bir bilgi tabani olusturuldu.

### Test Sonucu

Soru: "Boyali parcalarda pürüzlü bir yüzey görüyoruz, portakal
kabuğu gibi. Ne yapmaliyiz?"

Retrieval, alakasiz bir kaydi da (hidrolik basinc dususu) getirdi,
ancak Claude bunu doğru şekilde filtreleyip SADECE ilgili kayda
(elektrostatik toz boya - portakal kabugu) dayanarak dogru, adim
adim bir cozum uretti. Bu, retrieval mukemmel olmasa bile
generation'in (LLM) dogru bilgiyi secebildigini gosterdi.

## Ornek 3: CEO Karar Destek RAG (ceo_ornegi/)

Nakit akisi, insan kaynaklari, pazar genisleme ve operasyonel
verimlilik konularinda 8 kayitlik ust yonetim seviyesi karar destek
bilgi tabani olusturuldu.

### Test Sonucu

Soru: "Ihracat yaptigimiz Avrupa pazarinda kur dalgalanmasi kar
marjimizi eritiyor, ne yapmaliyiz?"

Claude, ham kayittaki maddeleri zaman bazli bir eylem planina
(0-3 ay / 3-6 ay) donusturdu ve somut yuzdelik oneriler (hedge orani
%60-70) ekleyerek ham bilgiyi profesyonel bir danismanlik formatina
sentezledi.

## Onemli Guvenlik Notu

Calisma sirasinda bir API anahtari yanlislikla bir sohbet arayuzune
yapistirilmis, hemen iptal edilip (revoke) yenisi olusturulmustur.
Ogrenilen ders: API anahtarlari SADECE terminal/kod icinde
kullanilmali, hicbir sohbet/log ortamina yazilmamalidir.

## Ogrenilen Ders

Ayni RAG mimarisi (embedding + vector db + LLM generation), tamamen
farkli uc alanda (biyoinformatik, imalat/kalite, yonetim danismanligi)
degisiklik gerektirmeden calisti - sadece "hangi dokumanlar" degisti,
"nasil calisiyor" ayni kaldi. Bu, RAG'in gercek gucunun spesifik bir
alana ozel olmamasi, herhangi bir bilgi tabanina uygulanabilir genel
bir teknik olmasi oldugunu gosterdi. Ayrica retrieval'in mukemmel
olmadigi durumlarda bile (alakasiz parca getirilmesi), LLM'in
gercek anlama/muhakeme yetenegi sayesinde dogru bilgiyi secip
sentezleyebildigi gozlemlendi.

## Dosyalar

- embedding_demo.py, build_index.py, rag_query.py - Pipeline dok. RAG
- fabrika_ornegi/ - Fabrika ariza/cozum RAG ornegi
- ceo_ornegi/ - CEO karar destek RAG ornegi
- chroma_db/ - Kalici vektor veritabani (3 koleksiyon: pipeline_docs,
  fabrika_ariza_cozum, ceo_karar_destek) - gitignore'a eklendi
