# Hafta 5: Somatic Variant Calling (Mutect2 + VarDict)

## Özet

Gerçek tumor-normal exome verisi (HCC-benzeri, Exome_Tumor/Exome_Normal,
chr17) üzerinde GATK4 Mutect2 ve VarDict ile somatic variant calling
yapıldı, sonuçlar karşılaştırıldı ve IGV ile görsel olarak doğrulandı.

Veri kaynağı: chr17 tumor/normal exome BAM çifti (bwa-mem2 ile hizalanmış,
GRCh38, WUGSC), storage.googleapis.com/bfx_workshop_tmp üzerinden.

## Mutect2 Sonuçları

- 880 ham aday varyant → FilterMutectCalls sonrası **190 PASS**
- En dikkat çekici bulgu: **chr17:7,675,088 C>T** (TP53, R175H)
  - Normal: 0/0 (30 ref, 0 alt)
  - Tumor: 0/1 (0 ref, 40 alt, AF=0.977)
  - TLOD=137.4

## VarDict Sonuçları (TP53 bölgesi, chr17:7,668,402-7,687,550)

4 "StrongSomaticSNV" adayı bulundu:
- chr17:7,675,088 C>T (AF~1.0) - Mutect2 ile ORTAK
- chr17:7,673,297 C>A (AF=0.023) - sadece VarDict
- chr17:7,674,246 G>T (AF=0.018) - sadece VarDict
- chr17:7,676,012 G>T (AF=0.017) - sadece VarDict

## Çapraz Doğrulama

### 1. ClinVar veritabanı kontrolü
chr17:7,675,088 C>T pozisyonu ClinVar'da doğrudan kayıtlı:
**NM_000546.5(TP53):c.524G>A (p.Arg175His)** - Li-Fraumeni sendromu ve
sporadik kanserlerle ilişkili, TP53'ün en sık görülen hotspot
mutasyonlarından biri (R175H).

### 2. IGV görsel doğrulama

| Pozisyon | Tumor Alt Okuma | Strand Dağılımı | Değerlendirme |
|---|---|---|---|
| chr17:7,675,088 | 41/41 (%100) | 11+, 30- (dengeli) | **Gerçek mutasyon** |
| chr17:7,673,297 | 2/86 (%2) | 2+, 0- (tek yön) | Artefakt (strand bias) |
| chr17:7,674,246 | 2/110 (%2) | 2+, 0- (tek yön) | Artefakt (strand bias) |
| chr17:7,676,012 | 2/120 (%2) | 0+, 2- (tek yön) | Artefakt (strand bias) |

**Sonuç:** VarDict'in 3 ek adayı, tek strand yönünden gelen düşük
frekanslı (~%2) okumalara dayanıyor - klasik strand bias artefaktı imzası.
GATK4 Mutect2'nin bu 3 pozisyonu aday olarak bile değerlendirmemesi
(tumor-lod-to-emit eşiği altında kalmaları nedeniyle) doğru davranış
olarak değerlendirildi.

## Öğrenilen Ders

İki farklı somatic caller'ın uyuşmadığı noktalarda, sonucu körü körüne
kabul etmek yerine (a) bilinen varyant veritabanlarıyla (ClinVar) çapraz
kontrol ve (b) IGV ile görsel/strand-bias incelemesi yapılması gerekiyor.
Yüksek hassasiyetli araçlar (VarDict) daha fazla yanlış pozitif üretme
eğiliminde olabiliyor; her iki aracın da PASS/StrongSomatic dediği bir
varyant bile ek doğrulama gerektirebilir.

## Kullanılan Komutlar

```bash
# Mutect2
gatk Mutect2 -R chr17.fa -I tumor.bam -I normal.bam \
  -tumor Exome_Tumor -normal Exome_Normal -O somatic_chr17.vcf.gz

gatk FilterMutectCalls -R chr17.fa -V somatic_chr17.vcf.gz \
  -O somatic_chr17_filtered.vcf.gz

# VarDict (TP53 bölgesi)
vardict-java -G chr17.fa -f 0.01 -N Exome_Tumor \
  -b "tumor.bam|normal.bam" -R chr17:7668402-7687550 \
  -c 1 -S 2 -E 3 -g 4 > vardict_tp53_raw.txt
```

## Çıktı Dosyaları

- `results/somatic_chr17_filtered.vcf.gz` - Mutect2 filtrelenmiş VCF
- `results/vardict_tp53_raw.txt` - VarDict ham çıktı
