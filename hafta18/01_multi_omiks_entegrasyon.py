import duckdb
import random

random.seed(42)

# --- Katman 1: DNA varyant verisi (Hafta 3-5'teki gibi) ---
with open("dna_varyantlari.csv", "w") as f:
    f.write("hasta_id,gen,mutasyon,af\n")
    hastalar_tp53_mut = [1, 3, 5, 7]
    hastalar_tp53_wt = [2, 4, 6, 8]
    for h in hastalar_tp53_mut:
        f.write(f"{h},TP53,R175H,0.97\n")
    for h in hastalar_tp53_wt:
        f.write(f"{h},TP53,WT,0.0\n")

# --- Katman 2: RNA-seq ekspresyon verisi (TP53'ün bilinen hedef genleri) ---
with open("rna_ekspresyon.csv", "w") as f:
    f.write("hasta_id,gen,tpm\n")
    hedef_genler = ["CDKN1A", "MDM2", "BAX"]
    for h in range(1, 9):
        tp53_mutant = h in hastalar_tp53_mut
        for gen in hedef_genler:
            if tp53_mutant:
                tpm = random.uniform(5, 20)
            else:
                tpm = random.uniform(50, 120)
            f.write(f"{h},{gen},{tpm:.1f}\n")

# --- Katman 3: Klinik metadata ---
with open("klinik_veri.csv", "w") as f:
    f.write("hasta_id,yas,evre,sagkalim_ay\n")
    for h in range(1, 9):
        tp53_mutant = h in hastalar_tp53_mut
        yas = random.randint(45, 75)
        evre = random.choice(["II", "III"]) if not tp53_mutant else random.choice(["III", "IV"])
        sagkalim = random.randint(36, 84) if not tp53_mutant else random.randint(8, 30)
        f.write(f"{h},{yas},{evre},{sagkalim}\n")

con = duckdb.connect()
con.execute("CREATE VIEW dna AS SELECT * FROM read_csv_auto('dna_varyantlari.csv')")
con.execute("CREATE VIEW rna AS SELECT * FROM read_csv_auto('rna_ekspresyon.csv')")
con.execute("CREATE VIEW klinik AS SELECT * FROM read_csv_auto('klinik_veri.csv')")

print("=== 1) Tek başına DNA verisi: hangi hastalarda TP53 mutant? ===")
print(con.execute("SELECT * FROM dna ORDER BY hasta_id").df())

print("\n=== 2) Multi-omiks JOIN: DNA durumu + RNA ekspresyonu + klinik seyir bir arada ===")
print(con.execute("""
    SELECT d.hasta_id, d.mutasyon AS tp53_durumu,
           r.gen, ROUND(r.tpm, 1) AS ekspresyon_tpm,
           k.evre, k.sagkalim_ay
    FROM dna d
    JOIN rna r ON d.hasta_id = r.hasta_id
    JOIN klinik k ON d.hasta_id = k.hasta_id
    WHERE r.gen = 'CDKN1A'
    ORDER BY d.mutasyon, d.hasta_id
""").df())

print("\n=== 3) Grup karşılaştırması: TP53 mutant vs WT - hedef gen ekspresyonu ===")
print(con.execute("""
    SELECT d.mutasyon AS tp53_durumu, r.gen,
           ROUND(AVG(r.tpm), 1) AS ort_ekspresyon,
           COUNT(DISTINCT d.hasta_id) AS hasta_sayisi
    FROM dna d
    JOIN rna r ON d.hasta_id = r.hasta_id
    GROUP BY d.mutasyon, r.gen
    ORDER BY r.gen, d.mutasyon
""").df())

print("\n=== 4) Üç katman birleşik: DNA-RNA-Klinik korelasyonu ===")
print(con.execute("""
    SELECT d.mutasyon AS tp53_durumu,
           ROUND(AVG(r.tpm), 1) AS ort_hedef_gen_ekspresyonu,
           ROUND(AVG(k.sagkalim_ay), 1) AS ort_sagkalim_ay
    FROM dna d
    JOIN rna r ON d.hasta_id = r.hasta_id
    JOIN klinik k ON d.hasta_id = k.hasta_id
    WHERE r.gen = 'CDKN1A'
    GROUP BY d.mutasyon
""").df())

con.close()