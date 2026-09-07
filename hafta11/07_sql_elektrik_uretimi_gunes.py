import duckdb
import random
from datetime import datetime, timedelta

random.seed(15)

# --- Saatlik elektrik üretim verisi (4 santral, 15 günlük) ---
with open("elektrik_uretim.csv", "w") as f:
    f.write("santral_id,zaman,uretim_mw,talep_mw\n")
    santraller = ["Santral_Ruzgar", "Santral_Dogalgaz", "Santral_Hidro", "Santral_Gunes"]
    baslangic = datetime(2026, 8, 1, 0, 0)

    for santral in santraller:
        zaman = baslangic
        for saat in range(15 * 24):  # 15 gün, saatlik
            gun_index = saat // 24
            saat_of_day = saat % 24

            # Rüzgar santralinde bilinçli veri boşluğu (gün 5, saat 10-14 arası sensör arızası)
            if santral == "Santral_Ruzgar" and gun_index == 5 and 10 <= saat_of_day <= 14:
                zaman += timedelta(hours=1)
                continue

            if santral == "Santral_Ruzgar":
                temel = 80 + 40 * (1 if saat_of_day < 6 or saat_of_day > 20 else 0.3)
                uretim = max(0, temel + random.gauss(0, 15))

            elif santral == "Santral_Dogalgaz":
                temel = 150 + 60 * (1 if 8 <= saat_of_day <= 20 else 0.2)
                uretim = max(0, temel + random.gauss(0, 10))

            elif santral == "Santral_Hidro":
                uretim = max(0, 200 + random.gauss(0, 5))

            else:  # Santral_Gunes - PV + CSP hibrit (Hami tesisi mantığı)
                if 6 <= saat_of_day <= 19:
                    gunduz_pozisyon = (saat_of_day - 6) / 13
                    import math
                    pv_uretim = 900 * math.sin(gunduz_pozisyon * math.pi) * random.uniform(0.85, 1.0)
                else:
                    pv_uretim = 0

                if 20 <= saat_of_day or saat_of_day <= 3:
                    csp_uretim = 100 * random.uniform(0.7, 1.0)
                else:
                    csp_uretim = 0

                uretim = max(0, pv_uretim + csp_uretim + random.gauss(0, 5))

            talep = uretim * random.uniform(0.85, 1.15) if uretim > 0 else random.uniform(50, 100)
            f.write(f"{santral},{zaman.strftime('%Y-%m-%d %H:%M')},{round(uretim,1)},{round(talep,1)}\n")
            zaman += timedelta(hours=1)

con = duckdb.connect()
con.execute("CREATE VIEW uretim AS SELECT *, CAST(zaman AS TIMESTAMP) AS zaman_ts FROM read_csv_auto('elektrik_uretim.csv')")

print("=== 1) Veri boşluğu (gap) tespiti ===")
print(con.execute("""
    WITH sirali AS (
        SELECT santral_id, zaman_ts,
               LAG(zaman_ts) OVER (PARTITION BY santral_id ORDER BY zaman_ts) AS onceki_zaman
        FROM uretim
    )
    SELECT santral_id, onceki_zaman AS bosluk_baslangic, zaman_ts AS bosluk_bitis,
           DATE_DIFF('hour', onceki_zaman, zaman_ts) AS bosluk_saat
    FROM sirali
    WHERE DATE_DIFF('hour', onceki_zaman, zaman_ts) > 1
    ORDER BY santral_id, zaman_ts
""").df())

print("\n=== 2) Güneş santralinin 24 saatlik profili (PV gündüz + CSP gece) ===")
print(con.execute("""
    SELECT strftime(zaman_ts, '%H:00') AS saat,
           ROUND(AVG(uretim_mw), 1) AS ortalama_uretim_mw
    FROM uretim
    WHERE santral_id = 'Santral_Gunes'
    GROUP BY saat
    ORDER BY saat
""").df())

print("\n=== 3) Gün batımından sonraki üretim: CSP'nin katkısı ne kadar? ===")
print(con.execute("""
    SELECT
        CASE
            WHEN strftime(zaman_ts, '%H')::INT BETWEEN 20 AND 23
              OR strftime(zaman_ts, '%H')::INT BETWEEN 0 AND 3
            THEN 'Gece (CSP dönemi, 20:00-04:00)'
            WHEN strftime(zaman_ts, '%H')::INT BETWEEN 6 AND 19
            THEN 'Gündüz (PV dönemi)'
            ELSE 'Diğer (karanlık, üretim yok)'
        END AS donem,
        COUNT(*) AS saat_sayisi,
        ROUND(AVG(uretim_mw), 1) AS ort_uretim_mw,
        ROUND(SUM(uretim_mw), 0) AS toplam_uretim_mwh
    FROM uretim
    WHERE santral_id = 'Santral_Gunes'
    GROUP BY donem
    ORDER BY toplam_uretim_mwh DESC
""").df())

print("\n=== 4) Tüm santrallerin günlük toplam üretimi (karşılaştırma) ===")
print(con.execute("""
    SELECT santral_id, DATE_TRUNC('day', zaman_ts) AS gun,
           ROUND(SUM(uretim_mw), 0) AS gunluk_toplam_mwh
    FROM uretim
    GROUP BY santral_id, gun
    ORDER BY gun, santral_id
    LIMIT 16
""").df())

print("\n=== 5) Arz-talep açığı: hangi santral/saatte açık en büyük? ===")
print(con.execute("""
    SELECT santral_id, zaman_ts, uretim_mw, talep_mw,
           ROUND(talep_mw - uretim_mw, 1) AS acik_mw
    FROM uretim
    WHERE talep_mw > uretim_mw * 1.1 AND uretim_mw > 0
    ORDER BY acik_mw DESC
    LIMIT 10
""").df())

con.close()