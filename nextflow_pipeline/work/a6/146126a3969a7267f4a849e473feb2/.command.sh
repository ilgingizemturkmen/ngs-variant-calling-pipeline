#!/bin/bash -ue
bwa index chr17.fa
samtools faidx chr17.fa
gatk CreateSequenceDictionary -R chr17.fa
