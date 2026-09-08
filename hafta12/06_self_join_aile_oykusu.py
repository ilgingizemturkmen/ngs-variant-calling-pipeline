import duckdb

con = duckdb.connect()

# --- Tek tablo: her hasta, kendi anne/baba hasta_id'sine referans verir ---
con.execute("""
    CREATE TABLE hastalar_aile (
        hasta_id INTEGER PRIMARY KEY,
        ad_soyad VARCHAR,
        anne_id INTEGER,
        baba_id INTEGER,
        tp53_durumu VARCHAR
    )
""")

con.execute("""
    INSERT INTO hastalar_aile VALUES
        (1, 'Ali Yilmaz (Buyukbaba)', NULL, NULL, 'MUT_R175H'),
        (2, 'Ayse Yilmaz (Buyukanne)', NULL, NULL, 'WT'),
        (3, 'Mehmet Yilmaz (Baba)', 2, 1, 'MUT_R175H'),
        (4, 'Fatma Kaya (Anne)', NULL, NULL, 'WT'),
        (5, 'Can Yilmaz (Cocuk 1)', 4, 3, 'MUT_R175H'),
        (6, 'Zeynep Yilmaz (Cocuk 2)', 4, 3, 'WT')
""")

print("=== 1) Ham tablo (henüz self-join yok) ===")
print(con.execute("SELECT * FROM hastalar_aile").df())

print("\n=== 2) Self-JOIN: her hastanın anne/baba adını yan yana göster ===")
print(con.execute("""
    SELECT
        cocuk.ad_soyad AS hasta,
        cocuk.tp53_durumu AS hasta_tp53,
        anne.ad_soyad AS anne_adi,
        anne.tp53_durumu AS anne_tp53,
        baba.ad_soyad AS baba_adi,
        baba.tp53_durumu AS baba_tp53
    FROM hastalar_aile cocuk
    LEFT JOIN hastalar_aile anne ON cocuk.anne_id = anne.hasta_id
    LEFT JOIN hastalar_aile baba ON cocuk.baba_id = baba.hasta_id
""").df())

print("\n=== 3) Kalıtım paterni analizi: baba mutasyonu taşıyorsa çocuğa geçme oranı ===")
print(con.execute("""
    SELECT
        baba.ad_soyad AS baba,
        baba.tp53_durumu AS baba_durumu,
        cocuk.ad_soyad AS cocuk,
        cocuk.tp53_durumu AS cocuk_durumu,
        CASE WHEN baba.tp53_durumu = cocuk.tp53_durumu THEN 'AYNI' ELSE 'FARKLI' END AS karsilastirma
    FROM hastalar_aile cocuk
    JOIN hastalar_aile baba ON cocuk.baba_id = baba.hasta_id
    WHERE baba.tp53_durumu = 'MUT_R175H'
""").df())

print("\n=== 4) Kaç nesil geriye gidiyoruz? (recursive CTE ile soy ağacı) ===")
print(con.execute("""
    WITH RECURSIVE soy_agaci AS (
        -- Başlangıç: Can Yilmaz'dan başla
        SELECT hasta_id, ad_soyad, anne_id, baba_id, 0 AS nesil
        FROM hastalar_aile
        WHERE hasta_id = 5

        UNION ALL

        -- Özyinelemeli kısım: babaya doğru yukarı çık
        SELECT h.hasta_id, h.ad_soyad, h.anne_id, h.baba_id, s.nesil + 1
        FROM hastalar_aile h
        JOIN soy_agaci s ON h.hasta_id = s.baba_id
    )
    SELECT * FROM soy_agaci ORDER BY nesil
""").df())

con.close()