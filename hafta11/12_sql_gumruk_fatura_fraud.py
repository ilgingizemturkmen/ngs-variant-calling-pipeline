import duckdb
import random
from datetime import datetime, timedelta

random.seed(88)

# --- Firmalar ---
with open("ithalatci_firmalar.csv", "w") as f:
    f.write("firma_id,firma_adi,sektor,ortalama_birim_fiyat_usd\n")
    firmalar = [
        (1, "F_Alfa_Tekstil", "Tekstil", 8.50),
        (2, "F_Beta_Elektronik", "Elektronik", 45.00),
        (3, "F_Gamma_Metal", "Metal", 3.20),
        (4, "F_Delta_Tekstil", "Tekstil", 8.20),
    ]
    for fid, ad, sektor, fiyat in firmalar:
        f.write(f"{fid},{ad},{sektor},{fiyat}\n")

# --- Gümrük beyanları ---
with open("gumruk_beyanlari.csv", "w") as f:
    f.write("beyan_id,firma_id,tarih,urun_kodu,miktar_kg,beyan_edilen_deger_usd,mensei_ulke\n")
    beyan_id = 1
    baslangic = datetime(2026, 1, 1)

    for fid, ad, sektor, birim_fiyat in firmalar:
        for _ in range(80):  # her firma için 80 beyan
            tarih = baslangic + timedelta(days=random.randint(0, 240))
            miktar = random.randint(500, 5000)
            # Normal durumda: deger = miktar * birim_fiyat (küçük varyasyonla)
            gercekci_deger = miktar * birim_fiyat * random.uniform(0.95, 1.05)
            urun_kodu = f"HS{random.randint(1000,9999)}"
            ulke = random.choice(["Cin", "Almanya", "Italya", "Hindistan", "Vietnam"])
            f.write(f"{beyan_id},{fid},{tarih.strftime('%Y-%m-%d')},{urun_kodu},{miktar},{round(gercekci_deger,2)},{ulke}\n")
            beyan_id += 1

    # --- Kasıtlı anomaliler: "under-invoicing" (düşük beyan) fraud paterni ---
    # F_Alfa_Tekstil, birkaç sevkiyatta gerçek değerin çok altında beyan veriyor (gümrük vergisi kaçırma)
    for _ in range(6):
        tarih = baslangic + timedelta(days=random.randint(0, 240))
        miktar = random.randint(2000, 4000)
        dusuk_deger = miktar * 8.5 * random.uniform(0.15, 0.30)  # gerçek değerin %15-30'u
        f.write(f"{beyan_id},1,{tarih.strftime('%Y-%m-%d')},HS5208,{miktar},{round(dusuk_deger,2)},Cin\n")
        beyan_id += 1

con = duckdb.connect()
con.execute("CREATE VIEW firmalar AS SELECT * FROM read_csv_auto('ithalatci_firmalar.csv')")
con.execute("CREATE VIEW beyanlar AS SELECT * FROM read_csv_auto('gumruk_beyanlari.csv')")

print("=== 1) Birim fiyat hesaplama + sektör ortalamasından sapma ===")
con.execute("""
    CREATE VIEW analiz AS
    SELECT b.*, f.firma_adi, f.sektor, f.ortalama_birim_fiyat_usd,
           ROUND(b.beyan_edilen_deger_usd / b.miktar_kg, 3) AS beyan_birim_fiyat
    FROM beyanlar b
    JOIN firmalar f ON b.firma_id = f.firma_id
""")
print(con.execute("SELECT * FROM analiz LIMIT 5").df())

print("\n=== 2) Subquery ile anomali tespiti: sektör ortalamasının çok altında birim fiyat ===")
print(con.execute("""
    SELECT firma_adi, beyan_id, tarih, miktar_kg, beyan_edilen_deger_usd, beyan_birim_fiyat
    FROM analiz
    WHERE beyan_birim_fiyat < (
        SELECT AVG(beyan_birim_fiyat) * 0.5
        FROM analiz a2
        WHERE a2.sektor = analiz.sektor
    )
    ORDER BY beyan_birim_fiyat
""").df())

print("\n=== 3) Aynı firmanın KENDİ geçmişiyle karşılaştırma (kendi ortalamasından sapma) ===")
print(con.execute("""
    SELECT firma_adi, beyan_id, tarih, beyan_birim_fiyat,
           ROUND((SELECT AVG(beyan_birim_fiyat) FROM analiz a2
                  WHERE a2.firma_id = analiz.firma_id), 3) AS firma_kendi_ortalamasi,
           ROUND(100.0 * beyan_birim_fiyat /
                 (SELECT AVG(beyan_birim_fiyat) FROM analiz a2
                  WHERE a2.firma_id = analiz.firma_id), 1) AS ortalamaya_gore_yuzde
    FROM analiz
    WHERE firma_id = 1
    ORDER BY beyan_birim_fiyat
    LIMIT 10
""").df())

print("\n=== 4) Vergi kaybı tahmini (basitleştirilmiş: %10 gümrük vergisi varsayımı) ===")
print(con.execute("""
    WITH supheli AS (
        SELECT *,
               (SELECT AVG(beyan_birim_fiyat) FROM analiz a2 WHERE a2.firma_id = analiz.firma_id) AS beklenen_birim_fiyat
        FROM analiz
        WHERE beyan_birim_fiyat < (
            SELECT AVG(beyan_birim_fiyat) * 0.5
            FROM analiz a3 WHERE a3.sektor = analiz.sektor
        )
    )
    SELECT firma_adi, beyan_id, miktar_kg,
           ROUND(miktar_kg * beklenen_birim_fiyat, 0) AS olmasi_gereken_deger,
           beyan_edilen_deger_usd AS beyan_edilen,
           ROUND((miktar_kg * beklenen_birim_fiyat - beyan_edilen_deger_usd) * 0.10, 0) AS tahmini_vergi_kaybi_usd
    FROM supheli
    ORDER BY tahmini_vergi_kaybi_usd DESC
""").df())

print("\n=== 5) Firma bazlı risk özeti ===")
print(con.execute("""
    SELECT f.firma_adi, f.sektor,
           COUNT(*) AS toplam_beyan,
           SUM(CASE WHEN a.beyan_birim_fiyat < (
               SELECT AVG(beyan_birim_fiyat) * 0.5 FROM analiz a2 WHERE a2.sektor = f.sektor
           ) THEN 1 ELSE 0 END) AS supheli_beyan_sayisi
    FROM analiz a
    JOIN firmalar f ON a.firma_id = f.firma_id
    GROUP BY f.firma_adi, f.sektor
    ORDER BY supheli_beyan_sayisi DESC
""").df())

con.close()