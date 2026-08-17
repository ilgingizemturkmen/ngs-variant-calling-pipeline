#!/bin/bash
# Kalite kontrol (FastQC + MultiQC)

mkdir -p fastqc_sonuclari

fastqc gercek_veri/*.fastq -o fastqc_sonuclari/

multiqc fastqc_sonuclari/ -o multiqc_sonuclari/
