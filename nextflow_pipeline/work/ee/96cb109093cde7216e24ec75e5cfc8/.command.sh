#!/bin/bash -ue
samtools faidx chr17.fa
gatk CreateSequenceDictionary -R chr17.fa
