import duckdb
import random

random.seed(21)

# --- Aynı malzeme tablosunu tekrar kullanıyoruz ---
with open("malzemeler.csv", "w") as f:
    f.write("malzeme_id,malzeme_adi,kalinlik_mm,birim_maliyet_tl\n")
    malzemeler = [(1, "Sac_2mm", 2.0, 45), (2, "Sac_3mm", 3.0, 68),
                  (3, "Sac_5mm", 5.0, 112), (4, "Paslanmaz_2mm", 2.0, 95)]
    for mid, ad, kalinlik, maliyet in malzemeler:
        f.write(f"{mid},{ad},{kalinlik},{maliyet}\n")

# --- Kesim işlemleri: bu kez her kesime bir "sapma_mm" değeri ekliyoruz ---
with open("lazer_kesim_detay.csv", "w") as f:
    f.write("islem_id,malzeme_id,hat,guc_watt,hiz_mm_s,hedef_olcu_mm,sapma_mm\n")
    islem_id = 1
    for _ in range(600):
        mid = random.choice([1, 2, 3, 4])
        hat = random.choice(["LAZER_1", "LAZER_2"])
        guc = random.randint(800, 2000)
        hiz = random.randint(10, 60)
        hedef_olcu = random.choice([300, 450, 600, 800])  # mm cinsinden parça uzunluğu

        # Fiziksel mantık: yüksek güç + düşük hız -> ısıl genleşme -> daha büyük sapma
        # yüksek hız -> titreşim/momentum kaynaklı sapma da artar (U-şekilli risk eğrisi)
        temel_sapma = abs((guc / 1000) - (hiz / 30)) * random.uniform(0.15, 0.35)
        gurultu = random.gauss(0, 0.1)
        sapma_mm = round(max(0, temel_sapma + gurultu), 3)

        f.write(f"{islem_id},{mid},{hat},{guc},{hiz},{hedef_olcu},{sapma_mm}\n")
        islem_id += 1

con = duckdb.connect()
con.execute("CREATE VIEW malzemeler AS SELECT * FROM read_csv_auto('malzemeler.csv')")
con.execute("CREATE VIEW kesim AS SELECT * FROM read_csv_auto('lazer_kesim_detay.csv')")

# --- Tolerans kuralı: ±0.5mm kabul edilebilir, üstü HURDA ---
TOLERANS_MM = 0.5

print(f"=== 1) Tolerans sınıflandırması (eşik: {TOLERANS_MM}mm) ===")
print(con.execute(f"""
    SELECT
        CASE WHEN sapma_mm <= {TOLERANS_MM} THEN 'KABUL' ELSE 'HURDA' END AS durum,
        COUNT(*) AS adet,
        ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS yuzde
    FROM kesim
    GROUP BY durum
""").df())

print("\n=== 2) Hurda maliyeti: malzeme bazlı ===")
print(con.execute(f"""
    SELECT m.malzeme_adi,
           COUNT(*) AS hurda_adet,
           ROUND(COUNT(*) * m.birim_maliyet_tl, 0) AS toplam_hurda_maliyet_tl
    FROM kesim k
    JOIN malzemeler m ON k.malzeme_id = m.malzeme_id
    WHERE k.sapma_mm > {TOLERANS_MM}
    GROUP BY m.malzeme_adi, m.birim_maliyet_tl
    ORDER BY toplam_hurda_maliyet_tl DESC
""").df())

print("\n=== 3) Hangi güç/hız aralığı hurda riskini artırıyor? (bucket analizi) ===")
print(con.execute(f"""
    SELECT
        CASE
            WHEN guc_watt < 1200 THEN 'Düşük Güç (<1200W)'
            WHEN guc_watt < 1600 THEN 'Orta Güç (1200-1600W)'
            ELSE 'Yüksek Güç (>1600W)'
        END AS guc_araligi,
        CASE
            WHEN hiz_mm_s < 25 THEN 'Düşük Hız (<25)'
            WHEN hiz_mm_s < 45 THEN 'Orta Hız (25-45)'
            ELSE 'Yüksek Hız (>45)'
        END AS hiz_araligi,
        COUNT(*) AS toplam_islem,
        SUM(CASE WHEN sapma_mm > {TOLERANS_MM} THEN 1 ELSE 0 END) AS hurda_adet,
        ROUND(100.0 * SUM(CASE WHEN sapma_mm > {TOLERANS_MM} THEN 1 ELSE 0 END) / COUNT(*), 1) AS hurda_yuzdesi
    FROM kesim
    GROUP BY guc_araligi, hiz_araligi
    ORDER BY hurda_yuzdesi DESC
""").df())

print("\n=== 4) Toplam mali özet ===")
print(con.execute(f"""
    SELECT
        SUM(CASE WHEN sapma_mm > {TOLERANS_MM} THEN 1 ELSE 0 END) AS toplam_hurda,
        COUNT(*) AS toplam_uretim,
        ROUND(100.0 * SUM(CASE WHEN sapma_mm > {TOLERANS_MM} THEN 1 ELSE 0 END) / COUNT(*), 1) AS hurda_orani_yuzde
    FROM kesim
""").df())

con.close()