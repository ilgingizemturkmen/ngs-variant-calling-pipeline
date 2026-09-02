#!/bin/bash -ue
samtools index NA12878.dedup.bam
gatk HaplotypeCaller -R chr17.fa -I NA12878.dedup.bam -O NA12878.vcf.gz
