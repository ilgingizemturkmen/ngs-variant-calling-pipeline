import duckdb
import time

con = duckdb.connect()

# --- PRIMARY KEY ile tablo ---
con.execute("""
    CREATE TABLE hasta_kayitlari (
        hasta_id INTEGER PRIMARY KEY,
        tc_no VARCHAR UNIQUE,
        ad_soyad VARCHAR
    )
""")

con.execute("INSERT INTO hasta_kayitlari VALUES (1, '12345678901', 'Ayse Kaya')")
con.execute("INSERT INTO hasta_kayitlari VALUES (2, '98765432109', 'Mehmet Demir')")

print("=== 1) Normal ekleme başarılı ===")
print(con.execute("SELECT * FROM hasta_kayitlari").df())

print("\n=== 2) Aynı hasta_id ile tekrar eklemeyi dene (PRIMARY KEY ihlali) ===")
try:
    con.execute("INSERT INTO hasta_kayitlari VALUES (1, '11111111111', 'Sahte Kayit')")
except Exception as e:
    print(f"HATA (beklenen): {type(e).__name__}: {e}")

print("\n=== 3) Aynı TC no ile farklı hasta_id eklemeyi dene (UNIQUE ihlali) ===")
try:
    con.execute("INSERT INTO hasta_kayitlari VALUES (3, '12345678901', 'Mukerrer TC')")
except Exception as e:
    print(f"HATA (beklenen): {type(e).__name__}: {e}")

print("\n=== 4) Tablo hala tutarlı mı? ===")
print(con.execute("SELECT * FROM hasta_kayitlari").df())

con.close()