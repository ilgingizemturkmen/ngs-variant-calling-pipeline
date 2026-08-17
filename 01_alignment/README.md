# Hafta 2: Alignment (BWA-mem)

## Özet

BWA-mem ile paired-end FASTQ verisini chr17 (GRCh38) referans genomuna
hizalama. Bu klasör hem başarılı sonucu hem de yol boyunca karşılaşılan
ve çözülen bir sorunu belgeliyor.

## Deneme 1: RNA-seq verisiyle (BAŞARISIZ)

İlk denemede SRR2121774 (TP53-null B-cells, GSE71176 RNA-seq verisi)
kullanıldı. Sonuç: **%0 mapping rate** - tüm okumalar unmapped (`*`)
olarak işaretlendi.

**Kok neden:** BWA-mem, DNA-seq icin tasarlanmis bir aligner - splice-aware
degil. RNA-seq okumalari exon-exon birlesim noktalarindan gecebilir
(intron'lar atlanir), bu yuzden dogrudan genomik pozisyona hizalanamaz.
Bu tur veri icin HISAT2/STAR gibi splice-aware aligner'lar gereklidir.

Kanit: `results/SRR2121774_bwa_FAILED_rnaseq_attempt.sam`

## Deneme 2: DNA-seq verisiyle (BAŞARILI)

Referans veri NA12878 (Genome in a Bottle, Broad Institute GATK test
bucket, `wgs_bam/NA12878_20k_hg38`) kullanildi. BAM'dan chr17 bolgesi
cikarilip (`samtools view -b ... chr17`) FASTQ'ya cevrildi
(`samtools fastq`), sonra BWA-mem ile hizalandi.

**Sonuc (samtools flagstat):**
- Toplam okuma: 1609
- Mapped: 1601 (%99.50)
- Properly paired: 1540 (%96.73)
- Singletons: 8 (%0.50)

Kanit: `results/NA12878_chr17_bwa.sam`

## Öğrenilen Ders

Aligner secimi veri tipine (DNA-seq vs RNA-seq) bagli olmali. Bu hata,
gercek bir klinik/arastirma ortaminda yanlis pipeline kullanimi
sonucu tum sonuclarin gecersiz olmasina yol acabilir - bu yuzden
pipeline'in basinda veri tipi dogrulamasi kritik bir adim.

## Kullanılan Komutlar

```bash
# BWA index (Hafta 1)
docker run --rm --platform linux/amd64 -v $(pwd)/data:/data \
  biocontainers/bwa:v0.7.17_cv1 bwa index /data/chr17.fa

# BAM'dan chr17 cikarma ve FASTQ'ya cevirme
samtools sort NA12878.bam -o NA12878_sorted.bam
samtools index NA12878_sorted.bam
samtools view -b NA12878_sorted.bam chr17 > NA12878_chr17.bam
samtools sort -n NA12878_chr17.bam -o NA12878_chr17_namesorted.bam
samtools fastq -1 NA12878_chr17_1.fastq -2 NA12878_chr17_2.fastq \
  -0 /dev/null -s /dev/null -n NA12878_chr17_namesorted.bam

# BWA-mem hizalama
docker run --rm --platform linux/amd64 -v $(pwd)/data:/data \
  biocontainers/bwa:v0.7.17_cv1 bwa mem /data/chr17.fa \
  /data/NA12878_chr17_1.fastq /data/NA12878_chr17_2.fastq > NA12878_chr17_bwa.sam

# Dogrulama
samtools flagstat NA12878_chr17_bwa.sam
```
