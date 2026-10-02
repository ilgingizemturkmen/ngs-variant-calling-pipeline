import duckdb
import random

random.seed(7)

# --- 4. Omiks katmanı: Protein bolluğu (kütle spektrometrisi tarzı, keyfi birim) ---
# Normalde RNA yüksekse protein de yüksek olmalı - ama GERÇEK HAYATTA her zaman böyle değil
with open("protein_bolluk.csv", "w") as f:
    f.write("hasta_id,protein,bolluk\n")
    # RNA verisini oku (önceki script'ten kalma dosya)
    import csv
    rna_tpm = {}
    with open("rna_ekspresyon.csv") as rf:
        for satir in csv.DictReader(rf):
            if satir["gen"] == "CDKN1A":
                rna_tpm[int(satir["hasta_id"])] = float(satir["tpm"])

    for hasta_id, tpm in rna_tpm.items():
        # Normal durum: protein, RNA ile orantılı (biraz gürültüyle)
        beklenen_protein = tpm * random.uniform(0.8, 1.2)

        # KASITLI ANOMALI: hasta 6 ve 8 (yüksek RNA, WT) için protein YAPAY OLARAK DÜŞÜK
        # (post-transkripsiyonel regülasyon / protein degradasyonu senaryosu)
        if hasta_id in [6, 8]:
            beklenen_protein = beklenen_protein * random.uniform(0.10, 0.20)

        f.write(f"{hasta_id},CDKN1A_protein,{beklenen_protein:.1f}\n")

con = duckdb.connect()
con.execute("CREATE VIEW dna AS SELECT * FROM read_csv_auto('dna_varyantlari.csv')")
con.execute("CREATE VIEW rna AS SELECT * FROM read_csv_auto('rna_ekspresyon.csv')")
con.execute("CREATE VIEW protein AS SELECT * FROM read_csv_auto('protein_bolluk.csv')")

print("=" * 60)
print("SORU: RNA yüksek olduğu halde protein seviyesi düşük çıkan hasta var mı?")
print("=" * 60)

print("\n=== 1) DNA + RNA + Protein - üç katman yan yana ===")
print(con.execute("""
    SELECT d.hasta_id, d.mutasyon AS tp53_durumu,
           ROUND(r.tpm, 1) AS rna_tpm,
           ROUND(p.bolluk, 1) AS protein_bolluk
    FROM dna d
    JOIN rna r ON d.hasta_id = r.hasta_id AND r.gen = 'CDKN1A'
    JOIN protein p ON d.hasta_id = p.hasta_id
    ORDER BY d.hasta_id
""").df())

print("\n=== 2) RNA-Protein oranı hesaplama: normalde ~1.0 civarı olmalı ===")
print(con.execute("""
    SELECT d.hasta_id, d.mutasyon AS tp53_durumu,
           ROUND(r.tpm, 1) AS rna_tpm,
           ROUND(p.bolluk, 1) AS protein_bolluk,
           ROUND(p.bolluk / r.tpm, 2) AS protein_rna_orani
    FROM dna d
    JOIN rna r ON d.hasta_id = r.hasta_id AND r.gen = 'CDKN1A'
    JOIN protein p ON d.hasta_id = p.hasta_id
    ORDER BY protein_rna_orani
""").df())

print("\n=== 3) CEVAP: Beklenenden çok düşük protein/RNA oranına sahip hastaları bul ===")
print("(Eşik: oran < 0.3 -> 'discordant', yani RNA-protein uyumsuz)")
print(con.execute("""
    SELECT d.hasta_id, d.mutasyon AS tp53_durumu,
           ROUND(r.tpm, 1) AS rna_tpm,
           ROUND(p.bolluk, 1) AS protein_bolluk,
           ROUND(p.bolluk / r.tpm, 2) AS protein_rna_orani,
           'DISCORDANT: RNA yuksek ama protein dusuk' AS yorum
    FROM dna d
    JOIN rna r ON d.hasta_id = r.hasta_id AND r.gen = 'CDKN1A'
    JOIN protein p ON d.hasta_id = p.hasta_id
    WHERE (p.bolluk / r.tpm) < 0.3 AND r.tpm > 40
    ORDER BY protein_rna_orani
""").df())

con.close()