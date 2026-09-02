#!/bin/bash -ue
gatk MarkDuplicates -I NA12878.sorted.bam -O NA12878.dedup.bam -M NA12878.dedup.metrics.txt
