import duckdb
import random
from datetime import datetime, timedelta

random.seed(15)

# --- Saatlik elektrik üretim verisi (3 santral, 15 günlük) ---
with open("elektrik_uretim.csv", "w") as f:
    f.write("santral_id,zaman,uretim_mw,talep_mw\n")
    santraller = ["Santral_Ruzgar", "Santral_Dogalgaz", "Santral_Hidro"]
    baslangic = datetime(2026, 8, 1, 0, 0)

    for santral in santraller:
        zaman = baslangic
        for saat in range(15 * 24):  # 15 gün, saatlik
            # Rüzgar santralinde bilinçli veri boşluğu bırakıyoruz (gün 5, saat 10-14 arası sensör arızası)
            gun_index = saat // 24
            saat_of_day = saat % 24

            if santral == "Santral_Ruzgar" and gun_index == 5 and 10 <= saat_of_day <= 14:
                zaman += timedelta(hours=1)
                continue  # bu saatler hiç yazılmıyor -> veri boşluğu (gap)

            if santral == "Santral_Ruzgar":
                # rüzgar üretimi saatlik dalgalı, gece daha güçlü rüzgar simülasyonu
                temel = 80 + 40 * (1 if saat_of_day < 6 or saat_of_day > 20 else 0.3)
                uretim = max(0, temel + random.gauss(0, 15))
            elif santral == "Santral_Dogalgaz":
                # doğalgaz talebe göre esnek çalışır, gündüz zirve
                temel = 150 + 60 * (1 if 8 <= saat_of_day <= 20 else 0.2)
                uretim = max(0, temel + random.gauss(0, 10))
            else:  # Hidro - stabil
                uretim = max(0, 200 + random.gauss(0, 5))

            talep = uretim * random.uniform(0.85, 1.15)
            f.write(f"{santral},{zaman.strftime('%Y-%m-%d %H:%M')},{round(uretim,1)},{round(talep,1)}\n")
            zaman += timedelta(hours=1)

con = duckdb.connect()
con.execute("CREATE VIEW uretim AS SELECT *, CAST(zaman AS TIMESTAMP) AS zaman_ts FROM read_csv_auto('elektrik_uretim.csv')")

print("=== 1) Veri boşluğu (gap) tespiti: saatlik kayıt eksik mi? ===")
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

print("\n=== 2) 24 saatlik hareketli ortalama üretim (rolling window) ===")
print(con.execute("""
    SELECT santral_id, zaman_ts, uretim_mw,
           ROUND(AVG(uretim_mw) OVER (
               PARTITION BY santral_id ORDER BY zaman_ts
               ROWS BETWEEN 23 PRECEDING AND CURRENT ROW
           ), 1) AS hareketli_24s_ortalama
    FROM uretim
    WHERE santral_id = 'Santral_Ruzgar'
    ORDER BY zaman_ts
    LIMIT 30
""").df())

print("\n=== 3) Arz-talep açığı: üretimin talebi karşılayamadığı saatler ===")
print(con.execute("""
    SELECT santral_id, zaman_ts, uretim_mw, talep_mw,
           ROUND(talep_mw - uretim_mw, 1) AS acik_mw
    FROM uretim
    WHERE talep_mw > uretim_mw * 1.1
    ORDER BY acik_mw DESC
    LIMIT 10
""").df())

print("\n=== 4) Santral bazlı günlük toplam üretim + gün-üstü karşılaştırma (LAG) ===")
print(con.execute("""
    WITH gunluk AS (
        SELECT santral_id, DATE_TRUNC('day', zaman_ts) AS gun,
               SUM(uretim_mw) AS gunluk_toplam_mwh
        FROM uretim
        GROUP BY santral_id, gun
    )
    SELECT santral_id, gun, ROUND(gunluk_toplam_mwh,0) AS bugun,
           ROUND(LAG(gunluk_toplam_mwh) OVER (PARTITION BY santral_id ORDER BY gun), 0) AS dun,
           ROUND(100.0 * (gunluk_toplam_mwh - LAG(gunluk_toplam_mwh) OVER (PARTITION BY santral_id ORDER BY gun))
                 / LAG(gunluk_toplam_mwh) OVER (PARTITION BY santral_id ORDER BY gun), 1) AS degisim_yuzde
    FROM gunluk
    WHERE santral_id = 'Santral_Ruzgar'
    ORDER BY gun
    LIMIT 10
""").df())

con.close()