import duckdb
import random
import time

random.seed(99)

con = duckdb.connect()

# --- Büyük ölçekli test tablosu: 500.000 test kaydı ---
print("500.000 satırlık test verisi üretiliyor...")
con.execute("""
    CREATE TABLE buyuk_testler (
        test_id INTEGER,
        numune_id INTEGER,
        hasta_id INTEGER,
        test_adi VARCHAR,
        sonuc VARCHAR,
        rapor_tarihi DATE
    )
""")

test_adlari = ["TP53_Sekans", "BRCA1_Sekans", "BRCA2_Sekans", "SMN1_Delesyon",
               "BCR-ABL1_Fusion", "EGFR_Sekans", "KRAS_Sekans"]
sonuclar = ["WT", "MUT_R175H", "MUT_OTHER", "POZITIF", "NEGATIF", "HOMOZIGOT_DEL"]

con.execute("BEGIN TRANSACTION")
for i in range(1, 500001):
    hasta_id = random.randint(1, 50000)  # 50.000 farklı hasta
    numune_id = random.randint(1, 150000)
    test_adi = random.choice(test_adlari)
    sonuc = random.choice(sonuclar)
    tarih = f"2026-{random.randint(1,8):02d}-{random.randint(1,28):02d}"
    con.execute("INSERT INTO buyuk_testler VALUES (?, ?, ?, ?, ?, ?)",
                [i, numune_id, hasta_id, test_adi, sonuc, tarih])
con.execute("COMMIT")

print("Veri üretimi tamamlandı.\n")

# --- İNDEKS YOKKEN sorgu süresi ---
print("=== 1) İndeks YOKKEN: belirli bir hasta_id'nin tüm testlerini bul ===")
hedef_hasta = 12345
t0 = time.time()
sonuc1 = con.execute(f"""
    SELECT * FROM buyuk_testler WHERE hasta_id = {hedef_hasta}
""").df()
t1 = time.time()
print(f"Bulunan kayıt: {len(sonuc1)}, Süre: {t1-t0:.4f} saniye")

# --- Şimdi İNDEKS oluştur ---
print("\n=== 2) hasta_id üzerine indeks oluşturuluyor ===")
con.execute("CREATE INDEX idx_hasta_id ON buyuk_testler(hasta_id)")
print("İndeks oluşturuldu.\n")

# --- İNDEKS VARKEN aynı sorgu ---
print("=== 3) İndeks VARKEN: aynı sorgu ===")
t0 = time.time()
sonuc2 = con.execute(f"""
    SELECT * FROM buyuk_testler WHERE hasta_id = {hedef_hasta}
""").df()
t1 = time.time()
print(f"Bulunan kayıt: {len(sonuc2)}, Süre: {t1-t0:.4f} saniye")

# --- Sonuçların aynı olduğunu doğrula ---
print(f"\nİki sorgu aynı sonucu mu verdi? {len(sonuc1) == len(sonuc2)}")

# --- EXPLAIN ile sorgu planını karşılaştır ---
print("\n=== 4) Sorgu planı (indeks kullanılıyor mu?) ===")
plan = con.execute(f"EXPLAIN SELECT * FROM buyuk_testler WHERE hasta_id = {hedef_hasta}").fetchall()
for row in plan:
    print(row[1] if len(row) > 1 else row)
    print("\n=== 5) Kontrol deneyi: indeks OLMADAN aynı sorguyu bir kez daha çalıştır ===")
con.execute("DROP INDEX idx_hasta_id")
t0 = time.time()
sonuc3 = con.execute(f"SELECT * FROM buyuk_testler WHERE hasta_id = {hedef_hasta}").df()
t1 = time.time()
print(f"Bulunan kayıt: {len(sonuc3)}, Süre: {t1-t0:.4f} saniye")

con.close()