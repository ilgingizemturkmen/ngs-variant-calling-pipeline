# Hafta 4: DeepVariant + Benchmark

## Özet

Ayni BAM dosyasi (NA12878, chr17) uzerinde hem GATK4 HaplotypeCaller hem
de DeepVariant calistirildi, sonuclar bcftools isec ile karsilastirildi
ve R/VennDiagram ile gorsellestirildi.

## Sonuclar

| Kategori | Sayi |
|---|---|
| Sadece GATK4 | 3 |
| Sadece DeepVariant | 15 |
| Ortak (her ikisinde) | 51 |
| GATK4 toplam | 54 |
| DeepVariant toplam | 66 |
| Jaccard uyum orani | 0.739 |

## Yorumlama

Iki arac varyantlarin %73.9'unda hemfikir. DeepVariant belirgin sekilde
daha fazla varyant buluyor (15 ekstra) - bu, literaturdeki genel bulguyla
ortusuyor: DeepVariant'in (derin ogrenme tabanli) hassasiyeti genellikle
GATK4'un istatistiksel modelinden daha yuksek, ozellikle dusuk derinlikli
bolgelerde ve indel'lerde.

## Kullanilan Araclar ve Komutlar

```bash
docker run --rm --platform linux/amd64 -v $(pwd)/data:/data google/deepvariant:1.6.1 \
  /opt/deepvariant/bin/run_deepvariant \
  --model_type=WGS --ref=/data/chr17.fa \
  --reads=/data/NA12878_chr17_dedup.bam \
  --output_vcf=/data/NA12878_chr17_deepvariant.vcf.gz --num_shards=4

bcftools index -t -f NA12878_chr17.vcf.gz
bcftools index -t -f NA12878_chr17_deepvariant.vcf.gz
bcftools isec -p isec_results NA12878_chr17.vcf.gz NA12878_chr17_deepvariant.vcf.gz

Rscript venn_comparison.R
```

## Cikti Dosyalari

- `results/gatk4_vs_deepvariant_venn.png` - Venn diyagrami
- `venn_comparison.R` - gorsellestirme scripti
