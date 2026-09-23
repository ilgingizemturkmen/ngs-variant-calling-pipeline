from Bio import Entrez

# --- NCBI, kim olduğunu bilmek istiyor (kötüye kullanımı önlemek için) ---
Entrez.email = "igzmbedir@gmail.com"  # kendi e-postan, NCBI kural gereği zorunlu

# =========================================================
# BÖLÜM 1: PubMed'de TP53 R175H ile ilgili makale arama
# =========================================================
print("=" * 60)
print("PubMed Araması: TP53 R175H")
print("=" * 60)

arama_terimi = "TP53 R175H mutation"
handle = Entrez.esearch(db="pubmed", term=arama_terimi, retmax=5)
sonuc = Entrez.read(handle)
handle.close()

print(f"Toplam bulunan makale sayısı: {sonuc['Count']}")
print(f"İlk 5 PubMed ID: {sonuc['IdList']}")

# --- Bu ID'lerin detaylarını (başlık, yazar, yıl) çekelim ---
if sonuc["IdList"]:
    handle = Entrez.esummary(db="pubmed", id=",".join(sonuc["IdList"]))
    ozetler = Entrez.read(handle)
    handle.close()

    print("\n--- İlk 5 makalenin özeti ---")
    for makale in ozetler:
        print(f"\nBaşlık: {makale.get('Title', 'N/A')}")
        print(f"Dergi: {makale.get('FullJournalName', 'N/A')}")
        print(f"Yıl: {makale.get('PubDate', 'N/A')}")

# =========================================================
# BÖLÜM 2: ClinVar'da TP53 R175H varyant kaydını arama
# =========================================================
print("\n" + "=" * 60)
print("ClinVar Araması: TP53 R175H")
print("=" * 60)

handle = Entrez.esearch(db="clinvar", term="TP53[gene] AND R175H", retmax=3)
clinvar_sonuc = Entrez.read(handle)
handle.close()

print(f"Toplam bulunan ClinVar kaydı: {clinvar_sonuc['Count']}")
print(f"İlk ID'ler: {clinvar_sonuc['IdList']}")

# =========================================================
# BÖLÜM 3: Gene veritabanından TP53'ün resmi bilgilerini çekme
# =========================================================
print("\n" + "=" * 60)
print("NCBI Gene: TP53 Resmi Bilgileri")
print("=" * 60)

handle = Entrez.esearch(db="gene", term="TP53[gene] AND human[orgn]", retmax=1)
gene_sonuc = Entrez.read(handle)
handle.close()

if gene_sonuc["IdList"]:
    gene_id = gene_sonuc["IdList"][0]
    handle = Entrez.esummary(db="gene", id=gene_id)
    gene_ozet = Entrez.read(handle)
    handle.close()

    gene_bilgi = gene_ozet["DocumentSummarySet"]["DocumentSummary"][0]
    print(f"Gene ID: {gene_id}")
    print(f"Resmi Sembol: {gene_bilgi.get('Name', 'N/A')}")
    print(f"Tam Ad: {gene_bilgi.get('Description', 'N/A')}")
    print(f"Kromozom: {gene_bilgi.get('Chromosome', 'N/A')}")
    print(f"Konum: {gene_bilgi.get('MapLocation', 'N/A')}")