import duckdb
import random

random.seed(77)

# --- Radar iz (track) verisi: her satır bir "tespit edilen nesne" ---
# Gerçek etiket (gercek_sinif) laboratuvar/test ortamında bilinir (örn. kontrollü drone uçuşu, ADS-B ile uçak doğrulaması)
# Radar bunu BİLMEZ, sadece fiziksel ölçümleri (RCS, hız, irtifa, micro-doppler) görür ve tahmin yapar.
with open("radar_izleri.csv", "w") as f:
    f.write("iz_id,rcs_m2,hiz_ms,irtifa_m,micro_doppler_hz,gercek_sinif\n")
    iz_id = 1

    # 1) KUŞ: küçük RCS, düşük-orta hız, düşük irtifa, düzensiz/düşük micro-doppler (kanat çırpışı)
    for _ in range(150):
        rcs = round(random.uniform(0.001, 0.05), 4)
        hiz = round(random.uniform(5, 15), 1)
        irtifa = round(random.uniform(20, 200), 0)
        doppler = round(random.uniform(2, 40), 1)  # artık bazen yüksek çıkabiliyor (rüzgar/tür farkı)
        f.write(f"{iz_id},{rcs},{hiz},{irtifa},{doppler},KUS\n"); iz_id += 1

    # 2) DRONE: küçük RCS (kuşa yakın!), düşük hız, düşük irtifa, YÜKSEK micro-doppler (pervane RPM'i)
    for _ in range(150):
        rcs = round(random.uniform(0.005, 0.08), 4)
        hiz = round(random.uniform(3, 20), 1)
        irtifa = round(random.uniform(10, 150), 0)
        doppler = round(random.uniform(20, 300), 1)  # bazı küçük drone modelleri düşük RPM'de
        f.write(f"{iz_id},{rcs},{hiz},{irtifa},{doppler},DRONE\n"); iz_id += 1

    # 3) UÇAK: büyük RCS, yüksek hız, yüksek irtifa, micro-doppler yok/ihmal edilebilir
    for _ in range(100):
        rcs = round(random.uniform(5, 50), 2)
        hiz = round(random.uniform(150, 250), 1)
        irtifa = round(random.uniform(3000, 12000), 0)
        doppler = round(random.uniform(0, 1), 1)
        f.write(f"{iz_id},{rcs},{hiz},{irtifa},{doppler},UCAK\n"); iz_id += 1

    # 4) GÜRÜLTÜ/CLUTTER: çok küçük veya tutarsız RCS, hız ~0, değişken irtifa, micro-doppler yok
    for _ in range(100):
        rcs = round(random.uniform(0.0001, 0.01), 4)
        hiz = round(random.uniform(0, 3), 1)
        irtifa = round(random.uniform(0, 500), 0)
        doppler = round(random.uniform(0, 2), 1)
        f.write(f"{iz_id},{rcs},{hiz},{irtifa},{doppler},GURULTU\n"); iz_id += 1


con = duckdb.connect()
con.execute("CREATE VIEW izler AS SELECT * FROM read_csv_auto('radar_izleri.csv')")

print("=== 1) Sınıflandırma kural motoru (CASE WHEN) - radar bunu 'gercek_sinif' bilmeden tahmin ediyor ===")
con.execute("""
    CREATE VIEW tahminler AS
    SELECT *,
        CASE
            WHEN hiz_ms > 100 AND irtifa_m > 2000 THEN 'UCAK'
            WHEN rcs_m2 < 0.1 AND micro_doppler_hz > 50 THEN 'DRONE'
            WHEN rcs_m2 < 0.1 AND micro_doppler_hz BETWEEN 1 AND 50 AND hiz_ms > 3 THEN 'KUS'
            ELSE 'GURULTU'
        END AS tahmin_sinif
    FROM izler
""")
print(con.execute("SELECT iz_id, rcs_m2, hiz_ms, irtifa_m, micro_doppler_hz, gercek_sinif, tahmin_sinif FROM tahminler LIMIT 10").df())

print("\n=== 2) Confusion matrix (karışıklık matrisi): gerçek vs tahmin ===")
print(con.execute("""
    SELECT gercek_sinif, tahmin_sinif, COUNT(*) AS adet
    FROM tahminler
    GROUP BY gercek_sinif, tahmin_sinif
    ORDER BY gercek_sinif, adet DESC
""").df())

print("\n=== 3) Sınıf bazlı Precision / Recall ===")
print(con.execute("""
    WITH gercek_pozitif AS (
        SELECT tahmin_sinif AS sinif, COUNT(*) AS tp
        FROM tahminler WHERE gercek_sinif = tahmin_sinif
        GROUP BY tahmin_sinif
    ),
    tum_tahmin AS (
        SELECT tahmin_sinif AS sinif, COUNT(*) AS toplam_tahmin
        FROM tahminler GROUP BY tahmin_sinif
    ),
    tum_gercek AS (
        SELECT gercek_sinif AS sinif, COUNT(*) AS toplam_gercek
        FROM tahminler GROUP BY gercek_sinif
    )
    SELECT g.sinif,
           gp.tp,
           tt.toplam_tahmin,
           tg.toplam_gercek,
           ROUND(100.0 * gp.tp / tt.toplam_tahmin, 1) AS precision_yuzde,
           ROUND(100.0 * gp.tp / tg.toplam_gercek, 1) AS recall_yuzde
    FROM tum_gercek g
    JOIN tum_gercek tg ON g.sinif = tg.sinif
    JOIN tum_tahmin tt ON g.sinif = tt.sinif
    LEFT JOIN gercek_pozitif gp ON g.sinif = gp.sinif
    ORDER BY g.sinif
""").df())

print("\n=== 4) En kritik hata: DRONE iken KUS/GURULTU sanılan izler (güvenlik açısından en tehlikeli yanlış) ===")
print(con.execute("""
    SELECT iz_id, rcs_m2, hiz_ms, irtifa_m, micro_doppler_hz, tahmin_sinif
    FROM tahminler
    WHERE gercek_sinif = 'DRONE' AND tahmin_sinif != 'DRONE'
""").df())


print("\n=== 5) Kaçırılan drone sayısı - false negative oranı ===")
print(con.execute("""
    SELECT COUNT(*) AS toplam_drone,
           SUM(CASE WHEN tahmin_sinif != 'DRONE' THEN 1 ELSE 0 END) AS kacirilan_drone,
           ROUND(100.0 * SUM(CASE WHEN tahmin_sinif != 'DRONE' THEN 1 ELSE 0 END) / COUNT(*), 1) AS kacirilma_yuzdesi
    FROM tahminler
    WHERE gercek_sinif = 'DRONE'
""").df())

con.close()