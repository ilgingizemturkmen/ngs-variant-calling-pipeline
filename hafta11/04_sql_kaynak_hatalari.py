import duckdb
import random

random.seed(3)

# --- Kaynakçılar tablosu ---
with open("kaynakcilar.csv", "w") as f:
    f.write("kaynakci_id,ad,deneyim_yil\n")
    kaynakcilar = [(1, "K_Ahmet", 12), (2, "K_Mehmet", 2), (3, "K_Ayse", 8), (4, "K_Fatma", 1)]
    for kid, ad, deneyim in kaynakcilar:
        f.write(f"{kid},{ad},{deneyim}\n")

# --- Kaynak işlemleri tablosu ---
with open("kaynak_islemleri.csv", "w") as f:
    f.write("islem_id,kaynakci_id,tarih,akim_amper,malzeme_kalinlik_mm,hata_tipi\n")
    hata_tipleri_normal = ["YOK"]
    hata_tipleri_riskli = ["GOZENEK", "EKSIK_NUFUZIYET", "CATLAK", "YOK", "YOK"]
    islem_id = 1
    for gun in range(1, 21):
        for kid, ad, deneyim in kaynakcilar:
            n_islem = random.randint(15, 25)
            for _ in range(n_islem):
                akim = random.randint(90, 180)
                kalinlik = round(random.uniform(2, 10), 1)
                # Deneyimsiz kaynakçı (deneyim<3) + yüksek akım/kalın malzeme kombinasyonu -> hata riski artar
                if deneyim < 3 and akim > 150 and kalinlik > 6:
                    hata = random.choice(["GOZENEK", "EKSIK_NUFUZIYET", "CATLAK", "GOZENEK"])
                elif deneyim < 3:
                    hata = random.choice(hata_tipleri_riskli)
                else:
                    hata = random.choice(hata_tipleri_normal * 4 + ["GOZENEK"])
                f.write(f"{islem_id},{kid},2026-08-{gun:02d},{akim},{kalinlik},{hata}\n")
                islem_id += 1

con = duckdb.connect()
con.execute("CREATE VIEW kaynakcilar AS SELECT * FROM read_csv_auto('kaynakcilar.csv')")
con.execute("CREATE VIEW islemler AS SELECT * FROM read_csv_auto('kaynak_islemleri.csv')")

print("=== 1) Kaynakçı bazlı hata oranı (JOIN + CASE WHEN) ===")
print(con.execute("""
    SELECT k.ad, k.deneyim_yil,
           COUNT(*) AS toplam_islem,
           SUM(CASE WHEN i.hata_tipi != 'YOK' THEN 1 ELSE 0 END) AS hatali_islem,
           ROUND(100.0 * SUM(CASE WHEN i.hata_tipi != 'YOK' THEN 1 ELSE 0 END) / COUNT(*), 1) AS hata_yuzdesi
    FROM islemler i
    JOIN kaynakcilar k ON i.kaynakci_id = k.kaynakci_id
    GROUP BY k.ad, k.deneyim_yil
    ORDER BY hata_yuzdesi DESC
""").df())

print("\n=== 2) Hata tipi dağılımı, deneyim seviyesine göre ===")
print(con.execute("""
    SELECT
        CASE WHEN k.deneyim_yil < 3 THEN 'Junior (<3 yıl)' ELSE 'Senior (3+ yıl)' END AS seviye,
        i.hata_tipi,
        COUNT(*) AS adet
    FROM islemler i
    JOIN kaynakcilar k ON i.kaynakci_id = k.kaynakci_id
    WHERE i.hata_tipi != 'YOK'
    GROUP BY seviye, i.hata_tipi
    ORDER BY seviye, adet DESC
""").df())

print("\n=== 3) Riskli parametre kombinasyonu: yüksek akım + kalın malzeme + junior kaynakçı ===")
print(con.execute("""
    SELECT k.ad, i.akim_amper, i.malzeme_kalinlik_mm, i.hata_tipi
    FROM islemler i
    JOIN kaynakcilar k ON i.kaynakci_id = k.kaynakci_id
    WHERE k.deneyim_yil < 3 AND i.akim_amper > 150 AND i.malzeme_kalinlik_mm > 6
      AND i.hata_tipi != 'YOK'
    ORDER BY i.akim_amper DESC
    LIMIT 10
""").df())

con.close()