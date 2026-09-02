#!/bin/bash -ue
samtools index tumor.bam
samtools index normal.bam
gatk Mutect2 -R chr17.fa -I tumor.bam -I normal.bam -tumor Exome_Tumor -normal Exome_Normal -O somatic.vcf.gz
gatk IndexFeatureFile -I somatic.vcf.gz
