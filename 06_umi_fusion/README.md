# Hafta 7: fgbio (UMI) + STAR-Fusion

## Bölüm 1: fgbio UMI Pipeline

### Özet

Tumor exome BAM'ına sentetik UMI etiketleri eklenerek fgbio'nun standart
UMI consensus pipeline'i (SortBam -> GroupReadsByUmi -> CallMolecularConsensusReads)
basariyla calistirildi.

### Klinik Bağlam: MRD (Minimal/Measurable Residual Disease)

UMI (Unique Molecular Identifier) teknolojisi, gercek klinik pratikte en
cok **MRD tespiti** icin kullanilir. Tedavi sonrasi cok dusuk frekansli
(%0.01'e kadar) somatik mutasyonlari sequencing hatasindan ayirt etmek
icin her DNA fragmentine PCR oncesi benzersiz bir barkod eklenir. Ayni
UMI'ye sahip birden fazla okuma, ayni orijinal molekulden geldigini
gosterir - bu okumalarin "konsensus"u alinarak rastgele sequencing
hatalari elenir, gercek dusuk-frekansli mutasyonlar (MRD'nin kendisi)
guvenilir sekilde ayirt edilir.

### Sınırlama (Dürüstlük Notu)

Elimizdeki veri gercek UMI icermedigi icin (standart exome capture,
UMI-based kutuphane hazirlama protokolu degil), okuma adina dayali
**deterministik ama rastgele** sentetik UMI'lar uretildi (Python scripti
ile). Sonuc: "0 overlapping templates, 0 corrected templates (%0.00)"
- yani gercek bir hata duzeltme senaryosu simule edilemedi (her okuma
kendi basina benzersiz kaldi). Ancak fgbio'nun teknik pipeline adimlari
(SortBam, GroupReadsByUmi, CallMolecularConsensusReads) dogru sekilde
calistirildi ve dogrulandi.

### Kullanılan Komutlar

```bash
# Sentetik UMI ekleme (Python script)
samtools view -h tumor.bam | python3 add_synthetic_umi.py | samtools view -b -o tumor_with_umi.bam -

# fgbio pipeline
fgbio SortBam -i tumor_with_umi.bam -o tumor_umi_sorted.bam -s TemplateCoordinate
fgbio GroupReadsByUmi -i tumor_umi_sorted.bam -o tumor_umi_grouped.bam -s Adjacency
fgbio CallMolecularConsensusReads -i tumor_umi_grouped.bam -o tumor_umi_consensus.bam \
  --min-reads 1 --min-input-base-quality 20
```

---

## Bölüm 2: STAR-Fusion - BCR-ABL1 Tespiti

### Özet

K562 hücre hatti (Kronik Miyeloid Losemi'nin klasik BCR-ABL1/Philadelphia
kromozomu pozitif hucre hatti) test verisi kullanilarak STAR-Fusion ile
gen fuzyonu tespiti basariyla yapildi.

### Sonuç

| FusionName | JunctionReads | SpanningFrags | SpliceType | LargeAnchorSupport | FFPM |
|---|---|---|---|---|---|
| **BCR--ABL1** | 26 | 16 | ONLY_REF_SPLICE | YES_LDAS | 69,883.5 |

**ONLY_REF_SPLICE** ve **YES_LDAS**, en yuksek guven seviyesindeki fuzyon
cagrilarini gosteren etiketlerdir - kirilma noktasi bilinen bir referans
splice bolgesiyle birebir ortusuyor ve uzun capa (anchor) destegi var.

### Zorlu Yolculuk (Öğrenme Süreci)

Bu sonuca ulasmak icin uc farkli yaklasim denendi:

1. **Galaxy + manuel BLAST self-alignment** (chr9/chr22 minimal ozel
   referans) - teknik olarak calisti ama 0 fuzyon buldu. Kok neden:
   minimal/kesilmis referans, STAR'in chimeric alignment algoritmasi
   icin yetersiz genomik baglam sagliyor.

2. **Yerel Docker + resmi prep_genome_lib.pl** - dogru script bulundu
   ama `--dfam_db` parametresi (repeat masking icin) ~285MB'lik bir
   dosya indirmeyi gerektiriyordu, ev internetinde bu indirme
   makul olmayan sürede (16+ dakika, tamamlanmadan iptal edildi) kaldi.

3. **Google Colab (basarili)** - Colab'in hizli internet baglantisinda:
   - `condacolab` Python 3.13 uyumsuzlugu nedeniyle calismadi, bunun
     yerine Miniforge dogrudan bash ile kuruldu (izole ortam)
   - STAR-Fusion 1.7.0 (bioconda) kuruldu - bu surum `--dfam_db`
     parametresini hic desteklemiyor (daha basit/eski API)
   - `~/miniforge3/bin` PATH'e eklenerek STAR/BLAST araclari bulundu
   - **Kritik hata bulundu ve duzeltildi:** ilk GTF offset-duzeltme
     scriptimiz (`awk`) varsayilan alan ayiricisini (boşluk) kullanmis,
     GTF'nin 9. sutunundaki (`gene_id "X"; ...`) formatini bozup
     boşluklari tab'a cevirmisti. `awk -F'\t'` ile duzeltildi.
   - `prep_genome_lib.pl` ile CTAT genome lib basariyla insa edildi
     (ABL1 ve BCR genleri dogru sekilde index'lendi)
   - STAR-Fusion calistirildi, **BCR--ABL1 basariyla tespit edildi**

### Öğrenilen Ders

Bir bioinformatik pipeline'inda karsilasilan hata, cogunlukla tek bir
sebepten degil, birikimli kucuk sorunlardan (yanlis script yolu, format
uyumsuzlugu, kaynak kisitlari, versiyon farkliliklari) kaynaklanir.
Sistematik hata ayiklama (her hatayi tek tek izole edip cozmek) ve
gerektiginde platform degistirmek (yerel makine -> Galaxy -> Docker ->
Colab) gercek dunya bioinformatik calismasinin dogal bir parcasidir.

### Kullanılan Komutlar

```bash
# CTAT genome lib insaasi (Colab, Miniforge ortaminda)
prep_genome_lib.pl \
  --genome_fa bcr_abl1_regions.fa \
  --gtf bcr_abl1_offset_fixed.gtf \
  --max_readlength 150 \
  --output_dir ctat_genome_lib_build_dir \
  --CPU 2

# STAR-Fusion calistirma
STAR-Fusion \
  --left_fq K562f_1.fq.gz \
  --right_fq K562f_2.fq.gz \
  --genome_lib_dir ctat_genome_lib_build_dir \
  --output_dir star_fusion_outdir \
  --CPU 2
```

## Çıktı Dosyaları

- `results/bcr_abl1_fusion_result.tsv` - STAR-Fusion BCR-ABL1 tespiti sonucu
