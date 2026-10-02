import duckdb
from scipy import stats
import matplotlib.pyplot as plt

con = duckdb.connect()
con.execute("CREATE VIEW dna AS SELECT * FROM read_csv_auto('dna_varyantlari.csv')")
con.execute("CREATE VIEW rna AS SELECT * FROM read_csv_auto('rna_ekspresyon.csv')")
con.execute("CREATE VIEW klinik AS SELECT * FROM read_csv_auto('klinik_veri.csv')")

# --- Her hedef gen için TP53 mutant vs WT ekspresyon listelerini çek ---
hedef_genler = ["CDKN1A", "MDM2", "BAX"]

print("=" * 60)
print("İSTATİSTİKSEL ANLAMLILIK TESTİ (Bağımsız İki Örneklem t-testi)")
print("=" * 60)

sonuclar = {}
for gen in hedef_genler:
    mutant_degerler = con.execute(f"""
        SELECT r.tpm FROM rna r JOIN dna d ON r.hasta_id = d.hasta_id
        WHERE r.gen = '{gen}' AND d.mutasyon = 'R175H'
    """).df()["tpm"].tolist()

    wt_degerler = con.execute(f"""
        SELECT r.tpm FROM rna r JOIN dna d ON r.hasta_id = d.hasta_id
        WHERE r.gen = '{gen}' AND d.mutasyon = 'WT'
    """).df()["tpm"].tolist()

    # --- Bağımsız iki örneklem t-testi: iki grubun ortalaması gerçekten farklı mı? ---
    t_istatistigi, p_degeri = stats.ttest_ind(mutant_degerler, wt_degerler)

    sonuclar[gen] = {
        "mutant_ort": sum(mutant_degerler)/len(mutant_degerler),
        "wt_ort": sum(wt_degerler)/len(wt_degerler),
        "p_degeri": p_degeri,
        "mutant_degerler": mutant_degerler,
        "wt_degerler": wt_degerler,
    }

    anlamli_mi = "EVET (p < 0.05)" if p_degeri < 0.05 else "HAYIR (p >= 0.05)"
    print(f"\n{gen}:")
    print(f"  Mutant ortalama: {sonuclar[gen]['mutant_ort']:.1f} TPM")
    print(f"  WT ortalama: {sonuclar[gen]['wt_ort']:.1f} TPM")
    print(f"  t-istatistiği: {t_istatistigi:.3f}")
    print(f"  p-değeri: {p_degeri:.4f}")
    print(f"  İstatistiksel olarak anlamlı mı? {anlamli_mi}")

print("\n" + "=" * 60)
print("ÖNEMLİ METODOLOJİK NOT")
print("=" * 60)
print("""
n=4 (grup başına) çok küçük bir örneklem büyüklüğü. p-değeri anlamlı çıksa
bile, gerçek bir klinik/araştırma bağlamında bu sonuç TEK BAŞINA yeterli
kanıt SAYILMAZ - gerçek TCGA/klinik kohort çalışmaları genellikle
yüzlerce/binlerce hasta kullanır. Bu script'in amacı istatistiksel testin
NASIL uygulanacağını ve NASIL yorumlanacağını göstermek, küçük örneklemde
"anlamlı" çıkan bir sonucun klinik pratiğe aktarılabilir olduğunu iddia
etmek değil.
""")

# --- Görselleştirme: box plot ile grupları karşılaştır ---
fig, eksenler = plt.subplots(1, 3, figsize=(15, 5))
for i, gen in enumerate(hedef_genler):
    veri = [sonuclar[gen]["wt_degerler"], sonuclar[gen]["mutant_degerler"]]
    eksenler[i].boxplot(veri, tick_labels=["WT", "R175H"])
    eksenler[i].set_title(f"{gen}\np={sonuclar[gen]['p_degeri']:.4f}")
    eksenler[i].set_ylabel("TPM")

plt.tight_layout()
plt.savefig("tp53_hedef_gen_karsilastirma.png", dpi=150)
print("Grafik 'tp53_hedef_gen_karsilastirma.png' olarak kaydedildi.")

con.close()