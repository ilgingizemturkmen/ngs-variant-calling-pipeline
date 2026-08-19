# Hafta 3: Germline Variant Calling (GATK4)

## Özet

GATK4 HaplotypeCaller ile NA12878 chr17 verisi üzerinde germline
varyant çağırma. Hafta 2'nin çıktısı (BWA-mem alignment) üzerine inşa edildi.

## Ön İşleme Adımları

1. SAM → sıralı BAM (`samtools sort`)
2. Read Group ekleme (`gatk AddOrReplaceReadGroups`) - GATK'ın zorunlu
   tuttuğu örnek/lab/platform bilgisi
3. Duplicate marking (`gatk MarkDuplicates`) - 1609 kayıttan 0 duplikat
   bulundu (küçük/temiz veri seti)
4. BAM index'leme (`samtools index`)
5. Referans genom index'leme: `.fai` (`samtools faidx`) ve `.dict`
   (`gatk CreateSequenceDictionary`)

## Variant Calling

```bash
gatk HaplotypeCaller -R chr17.fa -I NA12878_chr17_dedup.bam -O NA12878_chr17.vcf.gz
```

**Sonuç:**
- 1609 okumadan 74'ü MappingQualityReadFilter ile elendi
- İşlem süresi: 0.31 dakika
- **54 varyant** çağrıldı (chr17'nin küçük bir bölümü için)

## Örnek Varyantlar

| Pozisyon | REF | ALT | Tip | Genotip |
|---|---|---|---|---|
| chr17:2925405 | T | A | SNP | 1/1 (homozigot) |
| chr17:7573600 | T | TC | Insertion | 1/1 (homozigot) |

Not: Bu veri setinde okuma derinliği düşük (DP=2), bu yüzden varyant
güvenilirliği sınırlı - gerçek klinik pipeline'da 30x+ derinlik beklenir.
Bu demo/öğrenme amaçlı küçük veri seti için normal.

## Kullanılan Komutlar

Bkz. `commands.sh`
