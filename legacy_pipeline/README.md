# Legacy Pipeline (RNA-seq -> lncRNA Analizi)

Bu klasör, `ngs-variant-calling-pipeline` projesinden önce tamamlanan RNA-seq
pipeline'ının indirme/QC/trimleme/alignment adımlarını belgeler.

Veri: SRR2121774 (TP53-null B-cells, GSE71176), SRR8836894 (PC9, EGFR exon 19
delesyonlu, GSE129221)

## Adimlar

1. `01_download_sra.sh` - SRA Toolkit ile ham FASTQ indirme
2. `02_qc.sh` - FastQC + MultiQC ile kalite kontrol
3. `03_trimming.sh` - Trimmomatic ile adapter/dusuk kalite temizligi
4. `04_alignment_hisat2.sh` - HISAT2 ile alignment (RNA-seq, splice-aware)

## ngs-variant-calling-pipeline ile Fark

Bu eski pipeline HISAT2 kullaniyor (RNA-seq odakli, splice-aware alignment).
Yeni pipeline'da ayni temiz FASTQ verisi **BWA-mem** ile hizalaniyor (DNA-seq/
germline-somatic variant calling standardi). Ikisi arasindaki fark, RNA-seq'in
intron/exon sinirlarini hesaba katmasi, DNA-seq'in ise dogrudan genomik
pozisyona hizalama yapmasidir.

Arac secimleri (Homebrew Tier 2/3 kurulum sorunlari nedeniyle manuel kuruldu):
SRA Toolkit, FastQC v0.12.1, Trimmomatic v0.39, HISAT2 v2.2.1
