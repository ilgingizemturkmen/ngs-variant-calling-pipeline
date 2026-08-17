#!/bin/bash
# Ham FASTQ indirme (SRA Toolkit)
# SRR2121774: TP53-null B-cells (GSE71176)
# SRR8836894: PC9, EGFR exon 19 delesyonlu (GSE129221)

SRR_IDS=("SRR2121774" "SRR8836894")

for SRR in "${SRR_IDS[@]}"; do
    prefetch "$SRR" -O ./sra_data/
    fasterq-dump ./sra_data/"$SRR"/"$SRR".sra -O ./gercek_veri/ --split-files
done
