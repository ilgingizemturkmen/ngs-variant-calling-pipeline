import random
import csv

random.seed(42)

# --- 1. Sentetik chr17 GTF (GENCODE v50 formatına benzer) ---
# Gerçek TP53 chr17:7,668,402-7,687,550 (GRCh38) civarında + komşu genler
genes_chr17 = [
    ("TP53", 7661779, 7687550, "-"),
    ("WRAP53", 7688284, 7701090, "+"),
    ("EFNB3", 7727884, 7732515, "-"),
    ("ATP1B2", 7495371, 7503115, "-"),
    ("SAT2", 7458620, 7462636, "+"),
]

gtf_path = "chr17_synthetic_gencode_v50.gtf"
with open(gtf_path, "w") as f:
    f.write('##description: synthetic GENCODE-v50-style annotation (chr17 subset)\n')
    for gene, start, end, strand in genes_chr17:
        gene_id = f"ENSG{random.randint(10000000,99999999):011d}.{random.randint(1,15)}"
        attrs = f'gene_id "{gene_id}"; gene_name "{gene}"; gene_type "protein_coding";'
        f.write(f"chr17\tSYNTH\tgene\t{start}\t{end}\t.\t{strand}\t.\t{attrs}\n")

print(f"GTF yazıldı: {gtf_path}")