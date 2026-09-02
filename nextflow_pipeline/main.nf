#!/usr/bin/env nextflow

nextflow.enable.dsl=2

params.reads_1     = "$projectDir/../data/NA12878_chr17_1.fastq"
params.reads_2     = "$projectDir/../data/NA12878_chr17_2.fastq"
params.reference   = "$projectDir/../data/chr17.fa"
params.sample_name = "NA12878"
params.outdir      = "$projectDir/../data/nextflow_results"

process BWA_INDEX {
    tag "bwa indexing"
    container 'biocontainers/bwa:v0.7.17_cv1'

    input:
        path reference

    output:
        path "${reference}*", emit: bwa_index

    script:
    """
    bwa index ${reference}
    """
}

process PREPARE_REFERENCE_DICT {
    tag "samtools faidx + gatk dict"
    container 'broadinstitute/gatk:4.5.0.0'

    input:
        path reference

    output:
        path reference, emit: ref_fasta
        path "${reference}.fai", emit: ref_fai
        path "${reference.baseName}.dict", emit: ref_dict

    script:
    """
    samtools faidx ${reference}
    gatk CreateSequenceDictionary -R ${reference}
    """
}

process BWA_ALIGN {
    tag "aligning ${sample_name}"
    container 'biocontainers/bwa:v0.7.17_cv1'
    publishDir "${params.outdir}/01_alignment", mode: 'copy'

    input:
        path reference
        path bwa_index_files
        path reads_1
        path reads_2
        val sample_name

    output:
        path "${sample_name}.sam", emit: sam

    script:
    """
    bwa mem -t 2 -R "@RG\\tID:${sample_name}\\tSM:${sample_name}\\tPL:ILLUMINA" ${reference} ${reads_1} ${reads_2} > ${sample_name}.sam
    """
}

process SAM_TO_SORTED_BAM {
    tag "sorting bam"
    container 'biocontainers/samtools:v1.9-4-deb_cv1'
    publishDir "${params.outdir}/01_alignment", mode: 'copy'

    input:
        path sam

    output:
        path "${sam.simpleName}.sorted.bam", emit: bam
        path "${sam.simpleName}.sorted.bam.bai", emit: bai

    script:
    """
    samtools sort -o ${sam.simpleName}.sorted.bam ${sam}
    samtools index ${sam.simpleName}.sorted.bam
    """
}

process MARK_DUPLICATES {
    tag "marking duplicates"
    container 'broadinstitute/gatk:4.5.0.0'
    publishDir "${params.outdir}/02_dedup", mode: 'copy'

    input:
        path bam
        path bai

    output:
        path "${bam.simpleName}.dedup.bam", emit: dedup_bam
        path "${bam.simpleName}.dedup.metrics.txt", emit: metrics

    script:
    """
    gatk MarkDuplicates -I ${bam} -O ${bam.simpleName}.dedup.bam -M ${bam.simpleName}.dedup.metrics.txt
    """
}

process HAPLOTYPE_CALLER {
    tag "calling variants"
    container 'broadinstitute/gatk:4.5.0.0'
    publishDir "${params.outdir}/03_germline_variants", mode: 'copy'

    input:
        path reference
        path ref_fai
        path ref_dict
        path dedup_bam

    output:
        path "${dedup_bam.simpleName}.vcf.gz", emit: vcf

    script:
    """
    samtools index ${dedup_bam}
    gatk HaplotypeCaller -R ${reference} -I ${dedup_bam} -O ${dedup_bam.simpleName}.vcf.gz
    """
}

workflow {
    reference_ch = Channel.fromPath(params.reference, checkIfExists: true)
    reads_1_ch   = Channel.fromPath(params.reads_1, checkIfExists: true)
    reads_2_ch   = Channel.fromPath(params.reads_2, checkIfExists: true)

    BWA_INDEX(reference_ch)
    PREPARE_REFERENCE_DICT(reference_ch)

    BWA_ALIGN(
        PREPARE_REFERENCE_DICT.out.ref_fasta,
        BWA_INDEX.out.bwa_index,
        reads_1_ch,
        reads_2_ch,
        params.sample_name
    )

    SAM_TO_SORTED_BAM(BWA_ALIGN.out.sam)

    MARK_DUPLICATES(
        SAM_TO_SORTED_BAM.out.bam,
        SAM_TO_SORTED_BAM.out.bai
    )

    HAPLOTYPE_CALLER(
        PREPARE_REFERENCE_DICT.out.ref_fasta,
        PREPARE_REFERENCE_DICT.out.ref_fai,
        PREPARE_REFERENCE_DICT.out.ref_dict,
        MARK_DUPLICATES.out.dedup_bam
    )
}
