#!/bin/bash -ue
bwa mem -t 2 chr17.fa NA12878_chr17_1.fastq NA12878_chr17_2.fastq > NA12878.sam
