import duckdb
import random
from datetime import datetime, timedelta

random.seed(50)

# --- Satış verisi: 2 yıllık, 4 bölge, 3 ürün kategorisi ---
with open("satis_verisi.csv", "w") as f:
    f.write("tarih,bolge,kategori,gelir_tl,maliyet_tl\n")
    bolgeler = ["Ankara", "Istanbul", "Izmir", "Bursa"]
    kategoriler = ["Elektronik", "Mobilya", "Tekstil"]
    baslangic = datetime(2024, 9, 1)

    for ay_offset in range(24):  # 24 aylık veri (2 yıl)
        ay = baslangic + timedelta(days=30 * ay_offset)
        for bolge in bolgeler:
            for kategori in kategoriler:
                # Genel büyüme trendi + mevsimsellik (kasım-aralık zirve, ocak düşük)
                buyume_faktoru = 1 + (ay_offset * 0.015)  # zamanla büyüyen taban
                mevsim_ay = ay.month
                mevsim_carpan = 1.4 if mevsim_ay in (11, 12) else (0.75 if mevsim_ay == 1 else 1.0)

                temel_gelir = {"Elektronik": 180000, "Mobilya": 90000, "Tekstil": 60000}[kategori]
                bolge_carpan = {"Istanbul": 1.6, "Ankara": 1.2, "Izmir": 1.0, "Bursa": 0.8}[bolge]

                gelir = temel_gelir * bolge_carpan * buyume_faktoru * mevsim_carpan * random.uniform(0.9, 1.1)
                maliyet = gelir * random.uniform(0.55, 0.7)  # kar marjı ~%30-45

                f.write(f"{ay.strftime('%Y-%m-%d')},{bolge},{kategori},{round(gelir,0)},{round(maliyet,0)}\n")

con = duckdb.connect()
con.execute("CREATE VIEW satis AS SELECT *, CAST(tarih AS DATE) AS tarih_d FROM read_csv_auto('satis_verisi.csv')")

print("=== 1) Aylık toplam gelir/kar (temel CTE) ===")
print(con.execute("""
    WITH aylik AS (
        SELECT DATE_TRUNC('month', tarih_d) AS ay,
               SUM(gelir_tl) AS toplam_gelir,
               SUM(gelir_tl - maliyet_tl) AS toplam_kar
        FROM satis
        GROUP BY ay
    )
    SELECT ay, ROUND(toplam_gelir,0) AS gelir, ROUND(toplam_kar,0) AS kar,
           ROUND(100.0 * toplam_kar / toplam_gelir, 1) AS kar_marji_yuzde
    FROM aylik
    ORDER BY ay
    LIMIT 12
""").df())

print("\n=== 2) YoY (Year-over-Year) büyüme: bu ay vs geçen yıl aynı ay ===")
print(con.execute("""
    WITH aylik AS (
        SELECT DATE_TRUNC('month', tarih_d) AS ay, SUM(gelir_tl) AS gelir
        FROM satis GROUP BY ay
    )
    SELECT ay, ROUND(gelir,0) AS bu_ay_gelir,
           ROUND(LAG(gelir, 12) OVER (ORDER BY ay), 0) AS gecen_yil_ayni_ay,
           ROUND(100.0 * (gelir - LAG(gelir, 12) OVER (ORDER BY ay))
                 / LAG(gelir, 12) OVER (ORDER BY ay), 1) AS yoy_buyume_yuzde
    FROM aylik
    ORDER BY ay
""").df())

print("\n=== 3) Bölge sıralaması: her ay en çok kazanan bölge (RANK) ===")
print(con.execute("""
    WITH bolge_aylik AS (
        SELECT DATE_TRUNC('month', tarih_d) AS ay, bolge, SUM(gelir_tl) AS gelir
        FROM satis GROUP BY ay, bolge
    )
    SELECT ay, bolge, ROUND(gelir,0) AS gelir,
           RANK() OVER (PARTITION BY ay ORDER BY gelir DESC) AS siralama
    FROM bolge_aylik
    QUALIFY siralama = 1
    ORDER BY ay
    LIMIT 12
""").df())

print("\n=== 4) Kategori bazlı kar marjı karşılaştırması (CEO'nun sorabileceği soru) ===")
print(con.execute("""
    SELECT kategori,
           ROUND(SUM(gelir_tl),0) AS toplam_gelir,
           ROUND(SUM(gelir_tl - maliyet_tl),0) AS toplam_kar,
           ROUND(100.0 * SUM(gelir_tl - maliyet_tl) / SUM(gelir_tl), 1) AS kar_marji_yuzde
    FROM satis
    GROUP BY kategori
    ORDER BY kar_marji_yuzde DESC
""").df())

print("\n=== 5) Çok katmanlı CTE: 'En hızlı büyüyen bölge-kategori kombinasyonu' ===")
print(con.execute("""
    WITH ilk_yil AS (
        SELECT bolge, kategori, SUM(gelir_tl) AS gelir_ilk_yil
        FROM satis WHERE tarih_d < '2025-09-01'
        GROUP BY bolge, kategori
    ),
    ikinci_yil AS (
        SELECT bolge, kategori, SUM(gelir_tl) AS gelir_ikinci_yil
        FROM satis WHERE tarih_d >= '2025-09-01'
        GROUP BY bolge, kategori
    )
    SELECT i1.bolge, i1.kategori,
           ROUND(i1.gelir_ilk_yil,0) AS yil1,
           ROUND(i2.gelir_ikinci_yil,0) AS yil2,
           ROUND(100.0 * (i2.gelir_ikinci_yil - i1.gelir_ilk_yil) / i1.gelir_ilk_yil, 1) AS buyume_yuzde
    FROM ilk_yil i1
    JOIN ikinci_yil i2 ON i1.bolge = i2.bolge AND i1.kategori = i2.kategori
    ORDER BY buyume_yuzde DESC
""").df())

con.close()