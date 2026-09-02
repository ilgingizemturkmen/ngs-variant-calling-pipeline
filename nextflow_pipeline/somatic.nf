#!/usr/bin/env nextflow
nextflow.enable.dsl=2

params.tumor_bam    = "$projectDir/../data/inputs/tumor.bam"
params.normal_bam   = "$projectDir/../data/inputs/normal.bam"
params.reference    = "$projectDir/../data/inputs/chr17.fa"
params.outdir       = "$projectDir/../data/nextflow_results"

process PREPARE_REFERENCE {
    tag "preparing reference"
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

process MUTECT2_CALL {
    tag "somatic calling"
    container 'broadinstitute/gatk:4.5.0.0'
    publishDir "${params.outdir}/04_somatic_variants", mode: 'copy'

    input:
        path reference
        path ref_fai
        path ref_dict
        path tumor_bam
        path normal_bam

    output:
        path "somatic.vcf.gz", emit: vcf
        path "somatic.vcf.gz.stats", emit: stats
        path "somatic.vcf.gz.tbi", emit: vcf_index

    script:
    """
    samtools index ${tumor_bam}
    samtools index ${normal_bam}
    gatk Mutect2 -R ${reference} -I ${tumor_bam} -I ${normal_bam} -tumor Exome_Tumor -normal Exome_Normal -O somatic.vcf.gz
    gatk IndexFeatureFile -I somatic.vcf.gz
    """
}

process FILTER_MUTECT_CALLS {
    tag "filtering somatic calls"
    container 'broadinstitute/gatk:4.5.0.0'
    publishDir "${params.outdir}/04_somatic_variants", mode: 'copy'

    input:
        path reference
        path ref_fai
        path ref_dict
        path vcf
        path stats
        path vcf_index

    output:
        path "somatic_filtered.vcf.gz", emit: filtered_vcf

    script:
    """
    gatk FilterMutectCalls -R ${reference} -V ${vcf} -O somatic_filtered.vcf.gz
    """
}

workflow {
    reference_ch = Channel.fromPath(params.reference, checkIfExists: true)
    tumor_ch     = Channel.fromPath(params.tumor_bam, checkIfExists: true)
    normal_ch    = Channel.fromPath(params.normal_bam, checkIfExists: true)

    PREPARE_REFERENCE(reference_ch)

    MUTECT2_CALL(
        PREPARE_REFERENCE.out.ref_fasta,
        PREPARE_REFERENCE.out.ref_fai,
        PREPARE_REFERENCE.out.ref_dict,
        tumor_ch,
        normal_ch
    )

    FILTER_MUTECT_CALLS(
        PREPARE_REFERENCE.out.ref_fasta,
        PREPARE_REFERENCE.out.ref_fai,
        PREPARE_REFERENCE.out.ref_dict,
        MUTECT2_CALL.out.vcf,
        MUTECT2_CALL.out.stats,
        MUTECT2_CALL.out.vcf_index
    )
}
