import duckdb
import random

random.seed(7)

# --- Sentetik üretim hattı verisi (Aselsan/Roketsan tarzı QC senaryosu) ---
# Her satır: bir üretim vardiyasında, bir hatta üretilen parti + hata sayısı
with open("uretim_qc.csv", "w") as f:
    f.write("tarih,hat_id,vardiya,uretilen_adet,hatali_adet\n")
    hatlar = ["HAT_A", "HAT_B", "HAT_C"]
    for gun in range(1, 31):  # 30 günlük veri
        for hat in hatlar:
            for vardiya in ["Sabah", "Aksam", "Gece"]:
                uretilen = random.randint(80, 150)
                # HAT_B'de gün 20'den sonra bilinçli bir arıza trendi simüle ediyoruz
                hata_orani = 0.02
                if hat == "HAT_B" and gun > 20:
                    hata_orani = 0.02 + (gun - 20) * 0.015
                hatali = int(uretilen * hata_orani) + random.randint(0, 2)
                f.write(f"2026-08-{gun:02d},{hat},{vardiya},{uretilen},{hatali}\n")

con = duckdb.connect()
con.execute("CREATE VIEW qc AS SELECT * FROM read_csv_auto('uretim_qc.csv')")

print("=== 1) Günlük hata oranı (hat bazlı) ===")
print(con.execute("""
    SELECT tarih, hat_id,
           SUM(hatali_adet) AS toplam_hatali,
           SUM(uretilen_adet) AS toplam_uretilen,
           ROUND(100.0 * SUM(hatali_adet) / SUM(uretilen_adet), 2) AS hata_yuzdesi
    FROM qc
    GROUP BY tarih, hat_id
    ORDER BY hat_id, tarih
    LIMIT 10
""").df())

print("\n=== 2) 7 günlük hareketli ortalama hata oranı (window function) ===")
result = con.execute("""
    WITH gunluk AS (
        SELECT tarih, hat_id,
               100.0 * SUM(hatali_adet) / SUM(uretilen_adet) AS hata_yuzdesi
        FROM qc
        GROUP BY tarih, hat_id
    )
    SELECT tarih, hat_id,
           ROUND(hata_yuzdesi, 2) AS gunluk_hata,
           ROUND(AVG(hata_yuzdesi) OVER (
               PARTITION BY hat_id ORDER BY tarih
               ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
           ), 2) AS hareketli_7gun_ortalama
    FROM gunluk
    WHERE hat_id = 'HAT_B'
    ORDER BY tarih
""").df()
print(result)

print("\n=== 3) Anomali tespiti: hangi gün/hat, kendi ortalamasının 2 katından fazla hatalı? ===")
print(con.execute("""
    WITH gunluk AS (
        SELECT tarih, hat_id,
               100.0 * SUM(hatali_adet) / SUM(uretilen_adet) AS hata_yuzdesi
        FROM qc GROUP BY tarih, hat_id
    ),
    hat_ortalamalari AS (
        SELECT hat_id, AVG(hata_yuzdesi) AS ort_hata
        FROM gunluk GROUP BY hat_id
    )
    SELECT g.tarih, g.hat_id, ROUND(g.hata_yuzdesi,2) AS gunluk_hata,
           ROUND(h.ort_hata,2) AS hat_ortalamasi
    FROM gunluk g
    JOIN hat_ortalamalari h ON g.hat_id = h.hat_id
    WHERE g.hata_yuzdesi > 2 * h.ort_hata
    ORDER BY g.tarih
""").df())

con.close()