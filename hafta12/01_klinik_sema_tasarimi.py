import duckdb

con = duckdb.connect()

# --- 1. Hastalar tablosu (ana varlık) ---
con.execute("""
    CREATE TABLE hastalar (
        hasta_id INTEGER PRIMARY KEY,
        ad_soyad VARCHAR,
        dogum_tarihi DATE,
        cinsiyet VARCHAR
    )
""")

# --- 2. Numuneler tablosu (her hastanın birden fazla numunesi olabilir - 1:N ilişki) ---
con.execute("""
    CREATE TABLE numuneler (
        numune_id INTEGER PRIMARY KEY,
        hasta_id INTEGER,
        alinma_tarihi DATE,
        numune_tipi VARCHAR,
        FOREIGN KEY (hasta_id) REFERENCES hastalar(hasta_id)
    )
""")

# --- 3. Testler tablosu (her numuneden birden fazla test yapılabilir - 1:N ilişki) ---
con.execute("""
    CREATE TABLE testler (
        test_id INTEGER PRIMARY KEY,
        numune_id INTEGER,
        test_adi VARCHAR,
        sonuc VARCHAR,
        rapor_tarihi DATE,
        FOREIGN KEY (numune_id) REFERENCES numuneler(numune_id)
    )
""")

# --- Örnek veri ekle ---
con.execute("""
    INSERT INTO hastalar VALUES
        (1, 'Ayse Kaya', '1985-03-12', 'K'),
        (2, 'Mehmet Demir', '1990-07-25', 'E'),
        (3, 'Fatma Sahin', '1978-11-03', 'K')
""")

con.execute("""
    INSERT INTO numuneler VALUES
        (101, 1, '2026-01-10', 'Kan'),
        (102, 1, '2026-03-15', 'Kan'),
        (103, 2, '2026-02-01', 'Doku'),
        (104, 3, '2026-01-20', 'Kan')
""")

con.execute("""
    INSERT INTO testler VALUES
        (1001, 101, 'TP53_Sekans', 'MUT_R175H', '2026-01-15'),
        (1002, 101, 'BRCA1_Sekans', 'WT', '2026-01-16'),
        (1003, 102, 'TP53_Sekans', 'MUT_R175H', '2026-03-20'),
        (1004, 103, 'BCR-ABL1_Fusion', 'POZITIF', '2026-02-05'),
        (1005, 104, 'SMN1_Delesyon', 'HOMOZIGOT_DEL', '2026-01-25')
""")

print("=== Şema oluşturuldu, örnek veri eklendi ===\n")

# --- JOIN ile üç tabloyu birleştirip okunabilir rapor üretme ---
print("=== Hasta + Numune + Test - tam görünüm (3 tablo JOIN) ===")
print(con.execute("""
    SELECT h.ad_soyad, h.cinsiyet, n.alinma_tarihi, n.numune_tipi,
           t.test_adi, t.sonuc, t.rapor_tarihi
    FROM hastalar h
    JOIN numuneler n ON h.hasta_id = n.hasta_id
    JOIN testler t ON n.numune_id = t.numune_id
    ORDER BY h.ad_soyad, n.alinma_tarihi
""").df())

con.close()