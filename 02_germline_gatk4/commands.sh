#!/bin/bash
# Hafta 3: GATK4 Germline Variant Calling - tam komut sirasi

# On isleme
samtools sort NA12878_chr17_bwa.sam -o NA12878_chr17_sorted.bam
gatk AddOrReplaceReadGroups -I NA12878_chr17_sorted.bam -O NA12878_chr17_rg.bam \
  -RGID NA12878 -RGLB lib1 -RGPL illumina -RGPU unit1 -RGSM NA12878
gatk MarkDuplicates -I NA12878_chr17_rg.bam -O NA12878_chr17_dedup.bam -M dedup_metrics.txt
samtools index NA12878_chr17_dedup.bam

# Referans hazirlama
samtools faidx chr17.fa
gatk CreateSequenceDictionary -R chr17.fa

# Variant calling
gatk HaplotypeCaller -R chr17.fa -I NA12878_chr17_dedup.bam -O NA12878_chr17.vcf.gz
