#!/bin/bash
# Alignment (HISAT2) - eski RNA-seq pipeline
# Not: ngs-variant-calling-pipeline'da BWA-mem'e gecildi (DNA-seq/variant
# calling standardi). HISAT2 splice-aware, RNA-seq icin uygun; BWA-mem
# DNA-seq/germline-somatic variant calling icin standart.

SRR="SRR2121774"
CHR="chr17"

hisat2 -x "$CHR"_index -1 trimmomatic_sonuclari/"$SRR"_1_temiz.fastq \
       -2 trimmomatic_sonuclari/"$SRR"_2_temiz.fastq \
       -S "$SRR"_"$CHR".sam

samtools sort "$SRR"_"$CHR".sam -o "$SRR"_"$CHR"_sorted.bam
samtools index "$SRR"_"$CHR"_sorted.bam
