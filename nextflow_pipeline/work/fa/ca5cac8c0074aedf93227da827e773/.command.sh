#!/bin/bash -ue
bwa mem -t 2 -R "@RG\tID:NA12878\tSM:NA12878\tPL:ILLUMINA" chr17.fa NA12878_chr17_1.fastq NA12878_chr17_2.fastq > NA12878.sam
