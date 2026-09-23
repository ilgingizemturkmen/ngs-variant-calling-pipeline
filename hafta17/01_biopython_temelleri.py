from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio import SeqIO

# --- 1. Seq nesnesi: DNA/RNA/protein dizilerini temsil eden temel yapı ---
tp53_kismi_dizi = Seq("ATGGAGGAGCCGCAGTCAGATCCTAGCGTCGAGCCCCCTCTGAGTCAGGAAACATTTTCAGACCTATGGAAACTACTTCCTGAAAACAACGTTCTGTCCCCCTTGCCGTCCCAAGCAATGGATGATTTGATGCTGTCCCCGGACGATATTGAACAATGGTTCACTGAAGACCCAGGTCCAGATGAAGCTCCCAGAATGCCAGAGGCTGCTCCCCCCGTGGCCCCTGCACCAGCAGCTCCTACACCGGCGGCCCCTGCACCAGCCCCCTCCTGGCCCCTGTCATCTTCTGTCCCTTCCCAGAAAACCTACCAGGGCAGCTACGGTTTCCGTCTGGGCTTCTTGCATTCTGGGACAGCCAAGTCTGTGACTTGCACGTACTCCCCTGCCCTCAACAAGATGTTTTGCCAACTGGCCAAGACCTGCCCTGTGCAGCTGTGGGTTGATTCCACACCCCCGCCCGGCACCCGCGTCCGCGCCATGGCCATCTACAAGCAGTCACAGCACATGACGGAGGTTGTGAGGCGCTGCCCCCACCATGAGCGCTGCTCAGATAGCGATGGTCTGGCCCCTCCTCAGCATCTTATCCGAGTGGAAGGAAATTTGCGTGTGGAGTATTTGGATGACAGAAACACTTTTCGACATAGTGTGGTGGTGCCCTATGAGCCGCCTGAGGTTGGCTCTGACTGTACCACCATCCACTACAACTACATGTGTAACAGTTCCTGCATGGGCGGCATGAACCGGAGGCCCATCCTCACCATCATCACACTGGAAGACTCCAGTGGTAATCTACTGGGACGGAACAGCTTTGAGGTGCGTGTTTGTGCCTGTCCTGGGAGAGACCGGCGCACAGAGGAAGAGAATCTCCGCAAGAAAGGGGAGCCTCACCACGAGCTGCCCCCAGGGAGCACTAAGCGAGCACTGCCCAACAACACCAGCTCCTCTCCCCAGCCAAAGAAGAAACCACTGGATGGAGAATATTTCACCCTTCAGATCCGTGGGCGTGAGCGCTTCGAGATGTTCCGAGAGCTGAATGAGGCCTTGGAACTCAAGGATGCCCAGGCTGGGAAGGAGCCAGGGGGGAGCAGGGCTCACTCCAGCCACCTGAAGTCCAAAAAGGGTCAGTCTACCTCCCGCCATAAAAAACTCATGTTCAAGACAGAAGGGCCTGACTCAGACTGA")

print(f"Dizi uzunluğu: {len(tp53_kismi_dizi)} baz")
print(f"İlk 30 baz: {tp53_kismi_dizi[:30]}")

# --- 2. Temel dizi işlemleri ---
print(f"\nGC içeriği hesabı için G+C sayısı: {tp53_kismi_dizi.count('G') + tp53_kismi_dizi.count('C')}")
gc_yuzdesi = (tp53_kismi_dizi.count('G') + tp53_kismi_dizi.count('C')) / len(tp53_kismi_dizi) * 100
print(f"GC içeriği: %{gc_yuzdesi:.2f}")

# --- 3. Ters-komplement (reverse complement) - hizalama/primer tasarımında sık kullanılır ---
ters_komplement = tp53_kismi_dizi.reverse_complement()
print(f"\nTers-komplementin ilk 30 bazı: {ters_komplement[:30]}")

# --- 4. Transkripsiyon (DNA -> mRNA) ve Translasyon (mRNA -> Protein) ---
mrna = tp53_kismi_dizi.transcribe()
protein = tp53_kismi_dizi.translate()
print(f"\nmRNA'nın ilk 30 bazı: {mrna[:30]}")
print(f"Protein dizisinin ilk 20 aminoasiti: {protein[:20]}")

# --- 5. R175H mutasyonunu simüle etme: pozisyon 175'teki kodonu değiştirme ---
# Gerçek TP53 CDS'inde codon 175, nükleotid pozisyonu (175-1)*3 = 522'den başlar
kodon_baslangic = (175 - 1) * 3
orijinal_kodon = tp53_kismi_dizi[kodon_baslangic:kodon_baslangic+3]
print(f"\n175. kodon (orijinal, CGC=Arginin bekleniyor bu bölgede): {orijinal_kodon}")
print(f"Bu kodonun kodladığı aminoasit: {orijinal_kodon.translate()}")

# --- 6. SeqRecord: bir dizi + onun metadata'sı (ID, açıklama, vs.) ---
kayit = SeqRecord(
    tp53_kismi_dizi,
    id="TP53_CDS_partial",
    description="TP53 tumor suppressor gene, partial CDS (Hafta 17 pratik)"
)
print(f"\nSeqRecord özeti:\nID: {kayit.id}\nAçıklama: {kayit.description}\nUzunluk: {len(kayit.seq)}")

# --- 7. Bu kaydı bir FASTA dosyasına yazma ---
SeqIO.write(kayit, "tp53_partial_cds.fasta", "fasta")
print("\nFASTA dosyası 'tp53_partial_cds.fasta' olarak kaydedildi.")

# --- 8. Az önce yazdığımız FASTA'yı geri okuma (round-trip testi) ---
print("\n--- FASTA dosyasını geri okuyoruz ---")
for okunan_kayit in SeqIO.parse("tp53_partial_cds.fasta", "fasta"):
    print(f"Okunan ID: {okunan_kayit.id}")
    print(f"Okunan dizi uzunluğu: {len(okunan_kayit.seq)}")