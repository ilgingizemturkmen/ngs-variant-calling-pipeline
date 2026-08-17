# NGS Variant Calling Pipeline

Roche Diagnostics Türkiye "Bioinformatics Specialist" ilanına yönelik 15 haftalık
öğrenme ve portföy projesi.

## Durum: Hafta 1 tamamlandı ✓

Docker ortamı kuruldu, tüm variant calling araçları doğrulandı:
- BWA v0.7.17
- GATK4 v4.5.0.0
- DeepVariant v1.6.0
- CNVkit v0.9.14
- fgbio v2.2.1
- STAR-Fusion v1.13.0
- MSIsensor-pro v1.3.0 (conda, native ARM64 — MSIsensor2 Apple Silicon'da
  segfault verdiği için tercih edildi)

## Yapı

Her klasör, 15 haftalık planın bir aşamasına karşılık gelir (bkz. proje planı).

## Ortam

- Docker Desktop (Apple Silicon)
- Python, R
- macOS ARM64
