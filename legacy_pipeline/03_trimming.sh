#!/bin/bash
# Trimleme (Trimmomatic v0.39)
# SLIDINGWINDOW:4:20 -> 4 bazlik pencerede ortalama kalite 20 altina duserse kes
# MINLEN:36 -> 36 bazdan kisa okumalari at

SRR_IDS=("SRR2121774" "SRR8836894")

for SRR in "${SRR_IDS[@]}"; do
    java -jar trimmomatic-0.39.jar PE \
        gercek_veri/"$SRR"_1.fastq gercek_veri/"$SRR"_2.fastq \
        trimmomatic_sonuclari/"$SRR"_1_temiz.fastq trimmomatic_sonuclari/"$SRR"_1_atilan.fastq \
        trimmomatic_sonuclari/"$SRR"_2_temiz.fastq trimmomatic_sonuclari/"$SRR"_2_atilan.fastq \
        SLIDINGWINDOW:4:20 MINLEN:36
done
