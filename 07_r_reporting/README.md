# Hafta 9: R Programlama & Raporlama

## Ozet

Nextflow pipeline'inin (Hafta 8) urettigi germline ve somatic VCF
sonuclari, R (vcfR paketi) ile okunup gorsellestirildi ve tek bir
R Markdown (rapor.Rmd) raporunda birlestirildi.

## Kullanilan Araclar

- vcfR: VCF dosyalarini R'a okuma/ayristirma
- rmarkdown + pandoc: kod+metin+grafik iceren HTML rapor uretimi

## Uretilen Grafikler

1. germline_variant_types.png - NA12878 SNP/INDEL dagilimi (51 SNP, 3 INDEL)
2. germline_quality_dist.png - Germline varyant kalite skoru histogrami
3. somatic_filter_summary.png - Mutect2 filtreleme ozeti (880 aday -> 190 PASS)
4. somatic_tp53_highlight.png - TP53 R175H'nin PASS varyantlar icinde vurgulanmasi

## Karsilasilan ve Cozulen Sorunlar

- Mutect2 ciktisinda standart QUAL sutunu bos (".") - Mutect2 kendi
  guven skorunu (TLOD) INFO alaninda tutuyor. Regex ile
  (regexpr/regmatches) INFO sutunundan TLOD degeri cikarildi.
- HTML rapor derlemesi icin pandoc (>=2.8) gerekiyordu, sistemde
  kurulu degildi - Homebrew ile kuruldu.

## R Markdown Raporu (rapor.Rmd -> rapor.html)

Rapor su bolumleri iceriyor:
- Germline varyant analizi (54 varyant, SNP/INDEL dagilimi)
- Somatic varyant analizi (Mutect2 filtreleme ozeti)
- On plana cikan bulgu: TP53 R175H (knitr::kable ile tablo + vurgulu grafik)
- Sonuc ozeti

## Calistirma

```bash
Rscript -e 'rmarkdown::render("07_r_reporting/rapor.Rmd")'
open 07_r_reporting/rapor.html
```

## Ogrenilen Ders

R'in kendisi VCF dosyalarini okuyamiyor - ozel paketler (vcfR) gerekiyor,
tipki Python'da BioPython gibi. VCF'nin INFO sutunu tek bir metin
icinde bircok bilgiyi tasidigi icin (anahtar=deger;anahtar=deger formati),
belirli bir degeri (TLOD gibi) cikarmak icin regex (duzenli ifade)
kullanmak gerekiyor - bu, gercek dunya VCF isleme is akislarinda sik
karsilasilan bir durum.

## Dosyalar

- rapor.Rmd / rapor.html - Ana R Markdown raporu
- plot_germline.R, plot_somatic.R - Grafik uretim scriptleri
- *.png - Uretilen grafikler
