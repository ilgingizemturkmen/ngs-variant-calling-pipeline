import duckdb
import random
from datetime import datetime, timedelta

random.seed(33)

# --- Kart sahipleri ---
with open("kart_sahipleri.csv", "w") as f:
    f.write("musteri_id,ad,sehir,ortalama_aylik_harcama\n")
    musteriler = [
        (1, "M_Can", "Ankara", 8000),
        (2, "M_Elif", "Istanbul", 15000),
        (3, "M_Deniz", "Izmir", 5000),
        (4, "M_Zeynep", "Ankara", 12000),
        (5, "M_Burak", "Bursa", 6000),
    ]
    for mid, ad, sehir, ort in musteriler:
        f.write(f"{mid},{ad},{sehir},{ort}\n")

# --- İşlemler ---
with open("kart_islemleri.csv", "w") as f:
    f.write("islem_id,musteri_id,zaman,tutar,sehir,kategori\n")
    kategoriler = ["Market", "Restoran", "Akaryakit", "Elektronik", "Giyim", "ATM"]
    baslangic = datetime(2026, 8, 1, 0, 0)
    islem_id = 1

    for mid, ad, ana_sehir, ort_harcama in musteriler:
        zaman = baslangic
        for i in range(300):  # her müşteri için ~300 işlem, 30 gün boyunca
            zaman = baslangic + timedelta(hours=random.randint(0, 30*24))
            tutar = round(random.uniform(ort_harcama*0.01, ort_harcama*0.08), 2)
            sehir = ana_sehir
            kategori = random.choice(kategoriler)
            f.write(f"{islem_id},{mid},{zaman.strftime('%Y-%m-%d %H:%M')},{tutar},{sehir},{kategori}\n")
            islem_id += 1

    # --- Kasıtlı ANOMALİ işlemleri ekliyoruz ---
    # 1) M_Can (Ankara, ort. 8000TL/ay) - aniden çok yüksek tutarlı işlem
    f.write(f"{islem_id},1,2026-08-15 03:22,45000.00,Ankara,Elektronik\n"); islem_id += 1
    # 2) M_Deniz (Izmir) - aynı gün, farklı şehirde art arda işlemler (imkansız seyahat - "impossible travel")
    f.write(f"{islem_id},3,2026-08-20 14:00,320.00,Izmir,Market\n"); islem_id += 1
    f.write(f"{islem_id},3,2026-08-20 14:15,890.00,Istanbul,Elektronik\n"); islem_id += 1  # 15 dk sonra başka şehir!
    # 3) M_Burak (Bursa) - gece yarısı art arda çok sayıda küçük ATM çekimi (kart test etme paterni)
    for k in range(6):
        f.write(f"{islem_id},5,2026-08-10 02:{10+k*2:02d},50.00,Bursa,ATM\n"); islem_id += 1

con = duckdb.connect()
con.execute("CREATE VIEW musteriler AS SELECT * FROM read_csv_auto('kart_sahipleri.csv')")
con.execute("CREATE VIEW islemler AS SELECT *, CAST(zaman AS TIMESTAMP) AS zaman_ts FROM read_csv_auto('kart_islemleri.csv')")

print("=== 1) Anomali türü 1: Ortalama harcamanın çok üzerinde tekil işlem ===")
print(con.execute("""
    SELECT i.islem_id, m.ad, i.zaman_ts, i.tutar, m.ortalama_aylik_harcama,
           ROUND(i.tutar / m.ortalama_aylik_harcama, 2) AS orana_gore_kat
    FROM islemler i
    JOIN musteriler m ON i.musteri_id = m.musteri_id
    WHERE i.tutar > m.ortalama_aylik_harcama * 2
    ORDER BY orana_gore_kat DESC
""").df())

print("\n=== 2) Anomali türü 2: 'İmkansız seyahat' - kısa sürede farklı şehirde işlem ===")
print(con.execute("""
    WITH sirali AS (
        SELECT musteri_id, islem_id, zaman_ts, sehir, tutar,
               LAG(zaman_ts) OVER (PARTITION BY musteri_id ORDER BY zaman_ts) AS onceki_zaman,
               LAG(sehir) OVER (PARTITION BY musteri_id ORDER BY zaman_ts) AS onceki_sehir
        FROM islemler
    )
    SELECT musteri_id, onceki_sehir, sehir AS yeni_sehir,
           onceki_zaman, zaman_ts,
           DATE_DIFF('minute', onceki_zaman, zaman_ts) AS dakika_farki
    FROM sirali
    WHERE sehir != onceki_sehir
      AND DATE_DIFF('minute', onceki_zaman, zaman_ts) < 120
    ORDER BY dakika_farki
""").df())

print("\n=== 3) Anomali türü 3: Kısa sürede çok sayıda küçük tutarlı ATM işlemi (kart test paterni) ===")
print(con.execute("""
    WITH pencere AS (
        SELECT musteri_id, zaman_ts, tutar, kategori,
               COUNT(*) OVER (
                   PARTITION BY musteri_id
                   ORDER BY zaman_ts
                   RANGE BETWEEN INTERVAL 30 MINUTE PRECEDING AND CURRENT ROW
               ) AS son_30dk_islem_sayisi
        FROM islemler
        WHERE kategori = 'ATM'
    )
    SELECT musteri_id, zaman_ts, tutar, son_30dk_islem_sayisi
    FROM pencere
    WHERE son_30dk_islem_sayisi >= 4
    ORDER BY musteri_id, zaman_ts
""").df())

print("\n=== 4) Genel risk skoru: müşteri bazlı anomali sayısı özeti ===")
print(con.execute("""
    SELECT m.ad,
           COUNT(*) AS toplam_islem,
           SUM(CASE WHEN i.tutar > m.ortalama_aylik_harcama * 2 THEN 1 ELSE 0 END) AS yuksek_tutar_anomalisi,
           MAX(i.tutar) AS en_yuksek_islem
    FROM islemler i
    JOIN musteriler m ON i.musteri_id = m.musteri_id
    GROUP BY m.ad
    ORDER BY yuksek_tutar_anomalisi DESC
""").df())

con.close()