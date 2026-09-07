import duckdb

# --- 1. Sentetik varyant verisi (Hafta3'teki TP53 R175H bulgunu simüle ediyor) ---
with open("chr17_variants.csv", "w") as f:
    f.write("CHROM,POS,REF,ALT,AF\n")
    f.write("chr17,7675088,C,T,0.977\n")   # gerçek TP53 R175H konumun
    f.write("chr17,7690000,A,G,0.45\n")    # WRAP53 içine düşmeli
    f.write("chr17,7500000,G,C,0.12\n")    # ATP1B2 içine düşmeli
    f.write("chr17,9000000,T,A,0.30\n")    # hiçbir gene düşmemeli (aralık dışı)

# --- 2. DuckDB bağlantısı aç ---
con = duckdb.connect()

# --- 3. GTF dosyasını doğrudan sorgula ---
con.execute("""
    CREATE VIEW gtf AS
    SELECT * FROM read_csv(
        'chr17_synthetic_gencode_v50.gtf',
        delim='\t', header=False, skip=1, strict_mode=false,
        columns={'chrom':'VARCHAR','source':'VARCHAR','feature':'VARCHAR',
                 'start':'BIGINT','end':'BIGINT','score':'VARCHAR',
                 'strand':'VARCHAR','frame':'VARCHAR','attributes':'VARCHAR'}
    )
""")

# --- 4. attributes kolonundan gene_name'i regex ile çek ---
con.execute("""
    CREATE VIEW genes AS
    SELECT chrom, start, "end", strand,
           regexp_extract(attributes, 'gene_name "([^"]+)"', 1) AS gene_name
    FROM gtf
""")

print("=== Genler tablosu ===")
print(con.execute("SELECT * FROM genes ORDER BY start").df())

# --- 5. Varyant CSV'sini oku ---
con.execute("CREATE VIEW variants AS SELECT * FROM read_csv_auto('chr17_variants.csv')")

# --- 6. RANGE JOIN: her varyantı, POS'un içine düştüğü gene eşleştir ---
print("\n=== Varyant -> Gen eşleştirmesi (range join) ===")
result = con.execute("""
    SELECT v.CHROM, v.POS, v.REF, v.ALT, v.AF, g.gene_name
    FROM variants v
    LEFT JOIN genes g
      ON v.CHROM = g.chrom AND v.POS BETWEEN g.start AND g."end"
    ORDER BY v.POS
""").df()
print(result)

con.close()