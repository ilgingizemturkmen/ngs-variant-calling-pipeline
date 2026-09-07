import duckdb
import random
from datetime import datetime, timedelta

random.seed(42)

# --- Radar istasyonları ---
with open("radar_istasyonlari.csv", "w") as f:
    f.write("radar_id,konum,model,kurulum_yili\n")
    radarlar = [
        (1, "Sinir_Hatti_A", "RadarX-100", 2019),
        (2, "Sinir_Hatti_B", "RadarX-100", 2020),
        (3, "Sahil_Nokta_C", "RadarX-200", 2023),
    ]
    for rid, konum, model, yil in radarlar:
        f.write(f"{rid},{konum},{model},{yil}\n")

# --- Gömülü sistem telemetri verisi (her radar için saniyede bir örnekleme) ---
with open("radar_telemetri.csv", "w") as f:
    f.write("radar_id,zaman,cpu_sicaklik_c,besleme_gerilim_v,sinyal_gucu_db,hedef_tespit_sayisi\n")
    baslangic = datetime(2026, 8, 1, 0, 0, 0)

    for rid, konum, model, yil in radarlar:
        zaman = baslangic
        sicaklik_trend = 45.0
        for saniye in range(3600):
            if rid == 1 and saniye > 2000:
                sicaklik_trend += random.uniform(0.01, 0.03)
            else:
                sicaklik_trend += random.gauss(0, 0.05)
                sicaklik_trend = max(40, min(55, sicaklik_trend))

            cpu_sicaklik = round(sicaklik_trend + random.gauss(0, 0.3), 2)

            besleme_gerilim = round(28.0 + random.gauss(0, 0.15), 2)
            if rid == 2 and 1500 <= saniye <= 1520:
                besleme_gerilim = round(24.0 + random.gauss(0, 0.3), 2)

            sinyal_bozulma = max(0, (cpu_sicaklik - 50) * 0.8)
            sinyal_gucu = round(-60 - sinyal_bozulma + random.gauss(0, 1.5), 2)
            hedef_sayisi = max(0, int(random.gauss(5 - sinyal_bozulma * 0.3, 1.5)))

            f.write(f"{rid},{zaman.strftime('%Y-%m-%d %H:%M:%S')},{cpu_sicaklik},{besleme_gerilim},{sinyal_gucu},{hedef_sayisi}\n")
            zaman += timedelta(seconds=1)

con = duckdb.connect()
con.execute("CREATE VIEW radarlar AS SELECT * FROM read_csv_auto('radar_istasyonlari.csv')")
con.execute("CREATE VIEW telemetri AS SELECT *, CAST(zaman AS TIMESTAMP) AS zaman_ts FROM read_csv_auto('radar_telemetri.csv')")

print("=== 1) CPU sıcaklığında termal kaçak (thermal runaway) tespiti ===")
print(con.execute("""
    WITH dakikalik AS (
        SELECT radar_id, DATE_TRUNC('minute', zaman_ts) AS dakika,
               AVG(cpu_sicaklik_c) AS ort_sicaklik
        FROM telemetri
        GROUP BY radar_id, dakika
    ),
    trend AS (
        SELECT radar_id, dakika, ort_sicaklik,
               ort_sicaklik - LAG(ort_sicaklik, 5) OVER (
                   PARTITION BY radar_id ORDER BY dakika
               ) AS son_5dk_degisim
        FROM dakikalik
    )
    SELECT radar_id, dakika, ROUND(ort_sicaklik,1) AS sicaklik,
           ROUND(son_5dk_degisim,2) AS son_5dk_artis
    FROM trend
    WHERE son_5dk_degisim > 1.0
    ORDER BY radar_id, dakika
    LIMIT 10
""").df())

print("\n=== 2) Besleme gerilimi anomalisi (voltage sag/spike tespiti) ===")
print(con.execute("""
    SELECT r.konum, t.zaman_ts, t.besleme_gerilim_v
    FROM telemetri t
    JOIN radarlar r ON t.radar_id = r.radar_id
    WHERE t.besleme_gerilim_v NOT BETWEEN 27.0 AND 29.0
    ORDER BY t.zaman_ts
    LIMIT 10
""").df())

print("\n=== 3) Sıcaklık - sinyal kalitesi korelasyonu (fiziksel bağıntı doğrulama) ===")
print(con.execute("""
    SELECT
        CASE
            WHEN cpu_sicaklik_c < 48 THEN 'Normal (<48°C)'
            WHEN cpu_sicaklik_c < 55 THEN 'Yüksek (48-55°C)'
            ELSE 'Kritik (>55°C)'
        END AS sicaklik_bandi,
        COUNT(*) AS ornek_sayisi,
        ROUND(AVG(sinyal_gucu_db), 2) AS ort_sinyal_gucu_db,
        ROUND(AVG(hedef_tespit_sayisi), 2) AS ort_hedef_tespiti
    FROM telemetri
    WHERE radar_id = 1
    GROUP BY sicaklik_bandi
    ORDER BY sicaklik_bandi
""").df())

print("\n=== 4) Bakım önceliklendirme: hangi radar en riskli? ===")
print(con.execute("""
    SELECT r.konum, r.model, r.kurulum_yili,
           ROUND(MAX(t.cpu_sicaklik_c), 1) AS max_sicaklik,
           ROUND(MIN(t.besleme_gerilim_v), 2) AS min_gerilim,
           SUM(CASE WHEN t.cpu_sicaklik_c > 55 THEN 1 ELSE 0 END) AS kritik_sicaklik_saniye,
           SUM(CASE WHEN t.besleme_gerilim_v NOT BETWEEN 27.0 AND 29.0 THEN 1 ELSE 0 END) AS gerilim_anomali_saniye
    FROM telemetri t
    JOIN radarlar r ON t.radar_id = r.radar_id
    GROUP BY r.konum, r.model, r.kurulum_yili
    ORDER BY kritik_sicaklik_saniye DESC
""").df())

con.close()