# Hafta 8: Nextflow ile Uctan Uca Pipeline Otomasyonu

## Ozet

Hafta 1-7'de Docker ile elle calistirilan adimlar, Nextflow DSL2 ile
otomatiklestirildi ve tekrar calistirilabilir hale getirildi. Iki ayri
pipeline gelistirildi: germline (main.nf) ve somatic (somatic.nf).

## 1) nf-core/sarek Denemesi (Ertelendi)

Endustri standardi nf-core/sarek pipeline'i (Roche gibi sirketlerin
kullandigi, akran degerlendirmesinden gecmis bir workflow) denendi.
Ancak Agustos 2026 itibariyla Nextflow (25.x/26.x) ile nf-core
pipeline'larinin manifest.contributors formati arasinda guncel,
ekosistem-genelinde bir uyumluluk sorunu tespit edildi:

Invalid contribution type maintainer in manifest.contributors config option

Bu hatanin coklu cozum denemesi yapildi (farkli Nextflow surumleri,
farkli sarek surumleri, yerel config duzeltmesi) ama her calistirmada
GitHub'dan taze pipeline kopyasi cekildigi icin yerel duzeltmeler kalici
olmuyor. Ayni hata farkli nf-core pipeline'larinda (atacseq,
seqinspector) da bagimsiz kullanicilar tarafindan bildirilmis - bu,
kullaniciya ozel bir kurulum sorunu degil, guncel bir ekosistem hatasi.

Karar: Bu deneme dogrulanmis sekilde belgelendi, proje sonuna
(Hafta 16 sonrasi) tekrar denenmek uzere ertelendi.

## 2) Germline Pipeline (main.nf)

BWA-mem alignment -> GATK4 germline variant calling zincirini
otomatiklestiren, 5 process'ten olusan pipeline.

### Adimlar

BWA_INDEX -> PREPARE_REFERENCE_DICT -> BWA_ALIGN -> SAM_TO_SORTED_BAM -> MARK_DUPLICATES -> HAPLOTYPE_CALLER

### Karsilasilan ve Cozulen Sorunlar

- Docker etkinlestirme: nextflow.config ile docker.enabled = true
  ve Apple Silicon icin --platform linux/amd64 eklendi.
- Eksik referans dosyalari: GATK, .fai ve .dict dosyalarini
  zorunlu tutuyor - ayri bir PREPARE_REFERENCE_DICT process'i eklendi.
- "the sample list cannot be null or empty" hatasi: BWA-mem
  komutuna Read Group eklenmemis oldugu icin GATK ornegi taniyamiyordu -
  duzeltildi.

### Sonuc (Dogrulama)

NA12878/chr17 verisiyle calistirildi, 54 germline varyant bulundu -
Hafta 3'te elle yapilan calistirmayla birebir ayni sonuc.

## 3) Somatic Pipeline (somatic.nf)

Tumor/normal exome verisiyle Mutect2 tabanli somatic variant calling
zincirini otomatiklestiren, 3 process'ten olusan pipeline.

### Adimlar

PREPARE_REFERENCE -> MUTECT2_CALL -> FILTER_MUTECT_CALLS

### Karsilasilan ve Cozulen Sorun

- "index is required" hatasi: FilterMutectCalls, VCF dosyasinin
  index'lenmis (.tbi) olmasini zorunlu tutuyor - MUTECT2_CALL
  process'inin sonuna gatk IndexFeatureFile eklendi.

### Sonuc (Dogrulama)

Tumor/normal exome verisiyle calistirildi:
- 190 PASS varyant - Hafta 5'te elle yapilan calistirmayla birebir ayni sonuc
- TP53 R175H (chr17:7675088) ayni degerlerle (TLOD=137.40, Tumor AF=%97.7,
  Normal=0/0) basariyla yeniden tespit edildi

## Ogrenilen Ders

Nextflow'a gecis, klinik/kurumsal bir ortamda bir kere dogru kur, sonra
sonsuz kere guvenilir sekilde tekrar calistir prensibini somut olarak
gosterdi - elle yapilan analiz ile otomatiklestirilmis pipeline'in
sonuclarinin birebir eslesmesi, otomasyonun dogrulugunu kanitliyor.
Ayrica endustri-standardi bir arac (sarek) her zaman ilk denemede
calismayabilir - boyle durumlarda sorunu dogru teshis edip (ekosistem
sorunu vs. kendi hatasi ayrimi), alternatif bir yolla (kendi pipeline'ini
yazarak) ilerlemek gercek dunya bioinformatik pratiginin bir parcasidir.

## Kullanilan Komutlar

Germline:
cd nextflow_pipeline
nextflow run main.nf

Somatic:
nextflow run somatic.nf

## Dosyalar

- main.nf - Germline pipeline (NA12878/chr17)
- somatic.nf - Somatic pipeline (tumor/normal exome, TP53 R175H)
- nextflow.config - Docker/platform ayarlari
- samplesheet_germline.csv, samplesheet.csv - sarek denemesi icin hazirlanan (ertelendi)
