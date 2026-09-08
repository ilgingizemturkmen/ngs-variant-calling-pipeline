import duckdb

con = duckdb.connect()

con.execute("""
    CREATE TABLE test_sonuclari (
        test_id INTEGER,
        hasta_id INTEGER,
        test_adi VARCHAR,
        sonuc VARCHAR,
        tarih DATE
    )
""")

con.execute("""
    INSERT INTO test_sonuclari VALUES
        (1, 1, 'TP53_Sekans', 'MUT_R175H', '2026-01-10'),
        (2, 1, 'TP53_Sekans', 'MUT_R175H', '2026-02-10'),
        (3, 1, 'BRCA1_Sekans', 'WT', '2026-01-15'),
        (4, 2, 'TP53_Sekans', 'WT', '2026-01-12'),
        (5, 2, 'BRCA1_Sekans', 'WT', '2026-01-18'),
        (6, 3, 'TP53_Sekans', 'MUT_R175H', '2026-01-20'),
        (7, 3, 'TP53_Sekans', 'MUT_R175H', '2026-03-01'),
        (8, 3, 'TP53_Sekans', 'MUT_R175H', '2026-04-15'),
        (9, 4, 'BRCA2_Sekans', 'MUT_OTHER', '2026-01-22')
""")

print("=== 1) WHERE - satır bazlı filtreleme (gruplamadan ÖNCE çalışır) ===")
print(con.execute("""
    SELECT * FROM test_sonuclari
    WHERE test_adi = 'TP53_Sekans'
""").df())

print("\n=== 2) GROUP BY - hasta başına test sayısı ===")
print(con.execute("""
    SELECT hasta_id, COUNT(*) AS test_sayisi
    FROM test_sonuclari
    GROUP BY hasta_id
""").df())

print("\n=== 3) HAVING - grup bazlı filtreleme (gruplamadan SONRA çalışır) ===")
print(con.execute("""
    SELECT hasta_id, COUNT(*) AS test_sayisi
    FROM test_sonuclari
    GROUP BY hasta_id
    HAVING COUNT(*) >= 3
""").df())

print("\n=== 4) YANLIŞ kullanım denemesi: WHERE içinde COUNT(*) kullanmaya çalışmak ===")
try:
    con.execute("""
        SELECT hasta_id, COUNT(*) AS test_sayisi
        FROM test_sonuclari
        WHERE COUNT(*) >= 3
        GROUP BY hasta_id
    """).df()
except Exception as e:
    print(f"HATA (beklenen): {type(e).__name__}")
    print(f"Mesaj: {e}")

print("\n=== 5) WHERE + GROUP BY + HAVING birlikte (gerçekçi klinik soru) ===")
print("Soru: TP53 testi MUT_R175H çıkan, en az 2 kez test edilmiş hastalar kimler?")
print(con.execute("""
    SELECT hasta_id, COUNT(*) AS mutasyon_sayisi
    FROM test_sonuclari
    WHERE test_adi = 'TP53_Sekans' AND sonuc = 'MUT_R175H'
    GROUP BY hasta_id
    HAVING COUNT(*) >= 2
""").df())

con.close()