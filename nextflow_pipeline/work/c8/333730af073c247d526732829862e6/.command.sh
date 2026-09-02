#!/bin/bash -ue
gatk FilterMutectCalls -R chr17.fa -V somatic.vcf.gz -O somatic_filtered.vcf.gz
