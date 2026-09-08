import duckdb

con = duckdb.connect()

con.execute("""
    CREATE TABLE hasta_bakiye (
        hasta_id INTEGER PRIMARY KEY,
        ad_soyad VARCHAR,
        bakiye_tl DECIMAL(10,2)
    )
""")

con.execute("""
    INSERT INTO hasta_bakiye VALUES
        (1, 'Ayse Kaya', 500.00),
        (2, 'Mehmet Demir', 300.00)
""")

print("=== 1) Başlangıç durumu ===")
print(con.execute("SELECT * FROM hasta_bakiye").df())

# --- Senaryo: Ayse'den Mehmet'e 200 TL "transfer" yapıyoruz ---
# Bu iki ayrı UPDATE - eğer biri başarılı diğeri başarısız olursa, para "kaybolur" ya da "çoğalır"
print("\n=== 2) BAŞARISIZ transaction denemesi (kasıtlı hata ile) ===")
try:
    con.execute("BEGIN TRANSACTION")
    con.execute("UPDATE hasta_bakiye SET bakiye_tl = bakiye_tl - 200 WHERE hasta_id = 1")
    print("Adım 1 tamam: Ayse'den 200 TL düşüldü (henüz commit edilmedi)")

    # Kasıtlı hata: olmayan bir hasta_id'ye para eklemeye çalışıyoruz
    con.execute("UPDATE hasta_bakiye SET bakiye_tl = bakiye_tl + 200 WHERE hasta_id = 999")
    satir_sayisi = con.execute("SELECT COUNT(*) FROM hasta_bakiye WHERE hasta_id = 999").fetchone()[0]
    if satir_sayisi == 0:
        raise Exception("Hedef hasta bulunamadı! (hasta_id=999 mevcut değil)")

    con.execute("COMMIT")
except Exception as e:
    con.execute("ROLLBACK")
    print(f"HATA yakalandı: {e}")
    print("ROLLBACK yapıldı - hiçbir değişiklik kalıcı olmadı")

print("\n=== 3) Rollback sonrası durum: Ayse'nin parası GERİ GELDİ Mİ? ===")
print(con.execute("SELECT * FROM hasta_bakiye").df())

# --- Şimdi BAŞARILI bir transaction yapalım ---
print("\n=== 4) BAŞARILI transaction: Ayse'den Mehmet'e 200 TL transfer ===")
con.execute("BEGIN TRANSACTION")
con.execute("UPDATE hasta_bakiye SET bakiye_tl = bakiye_tl - 200 WHERE hasta_id = 1")
con.execute("UPDATE hasta_bakiye SET bakiye_tl = bakiye_tl + 200 WHERE hasta_id = 2")
con.execute("COMMIT")
print("Transaction başarılı, commit edildi")

print("\n=== 5) Son durum ===")
print(con.execute("SELECT * FROM hasta_bakiye").df())

con.close()