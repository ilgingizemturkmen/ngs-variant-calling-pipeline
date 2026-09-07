import duckdb
import random

random.seed(11)

# --- Malzeme tablosu (metal mobilya - masa ayağı tarzı parçalar) ---
with open("malzemeler.csv", "w") as f:
    f.write("malzeme_id,malzeme_adi,kalinlik_mm,birim_maliyet_tl\n")
    malzemeler = [(1, "Sac_2mm", 2.0, 45), (2, "Sac_3mm", 3.0, 68),
                  (3, "Sac_5mm", 5.0, 112), (4, "Paslanmaz_2mm", 2.0, 95)]
    for mid, ad, kalinlik, maliyet in malzemeler:
        f.write(f"{mid},{ad},{kalinlik},{maliyet}\n")

# --- Kesim işlemleri tablosu ---
with open("lazer_kesim.csv", "w") as f:
    f.write("islem_id,malzeme_id,hat,guc_watt,hiz_mm_s,hata_tipi\n")
    hata_yok = ["YOK"] * 6
    hatalar = ["YANIK_KENAR", "OLCU_SAPMASI", "TAM_KESILEMEDI"]
    islem_id = 1
    for _ in range(600):
        mid = random.choice([1, 2, 3, 4])
        hat = random.choice(["LAZER_1", "LAZER_2"])
        guc = random.randint(800, 2000)
        hiz = random.randint(10, 60)
        kalinlik = {1: 2.0, 2: 3.0, 3: 5.0, 4: 2.0}[mid]
        # Kalın malzemede düşük güç -> tam kesilemedi; yüksek hızda ince malzeme -> yanık kenar
        if kalinlik >= 5 and guc < 1200:
            hata = "TAM_KESILEMEDI"
        elif kalinlik <= 2 and hiz > 45:
            hata = "YANIK_KENAR"
        else:
            hata = random.choice(hata_yok + hatalar)
        f.write(f"{islem_id},{mid},{hat},{guc},{hiz},{hata}\n")
        islem_id += 1

con = duckdb.connect()
con.execute("CREATE VIEW malzemeler AS SELECT * FROM read_csv_auto('malzemeler.csv')")
con.execute("CREATE VIEW kesim AS SELECT * FROM read_csv_auto('lazer_kesim.csv')")

print("=== 1) Hata tipi + malzeme başına maliyet etkisi ===")
print(con.execute("""
    SELECT m.malzeme_adi, k.hata_tipi,
           COUNT(*) AS adet,
           ROUND(COUNT(*) * m.birim_maliyet_tl, 0) AS tahmini_kayip_tl
    FROM kesim k
    JOIN malzemeler m ON k.malzeme_id = m.malzeme_id
    WHERE k.hata_tipi != 'YOK'
    GROUP BY m.malzeme_adi, k.hata_tipi, m.birim_maliyet_tl
    ORDER BY tahmini_kayip_tl DESC
""").df())

print("\n=== 2) Hat bazlı hata oranı sıralaması (window function - RANK) ===")
print(con.execute("""
    SELECT hat, hata_tipi, COUNT(*) AS adet,
           RANK() OVER (PARTITION BY hat ORDER BY COUNT(*) DESC) AS siralama
    FROM kesim
    WHERE hata_tipi != 'YOK'
    GROUP BY hat, hata_tipi
    ORDER BY hat, siralama
""").df())

print("\n=== 3) Güç/hız parametrelerinin hataya etkisi (ortalama karşılaştırma) ===")
print(con.execute("""
    SELECT hata_tipi,
           ROUND(AVG(guc_watt), 0) AS ort_guc,
           ROUND(AVG(hiz_mm_s), 1) AS ort_hiz,
           COUNT(*) AS adet
    FROM kesim
    GROUP BY hata_tipi
    ORDER BY adet DESC
""").df())

con.close()