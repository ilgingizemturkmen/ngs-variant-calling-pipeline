#!/bin/bash -ue
samtools sort -o NA12878.sorted.bam NA12878.sam
samtools index NA12878.sorted.bam
