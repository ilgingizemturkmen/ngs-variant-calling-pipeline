# Hafta 6: CNV Analizi (CNVkit)

## Özet

Ayni tumor/normal exome cifti (chr17) uzerinde CNVkit ile kopya sayisi
degisimi (CNV) analizi yapildi. Sonuclar dogrulanirken onemli bir
metodolojik hata tespit edildi ve duzeltildi.

## İlk Analiz ve Sorun

CNVkit `--method wgs` ile calistirildi ve 7 CNV segmenti bulundu.
En carpici sonuc: chr17:37,007,418-67,106,764 araliginda **cn=1
(delesyon)** - bu bolgede **ERBB2 (HER2)** dahil onemli onkogenler var.

## Doğrulama Süreci

Bu 30 milyon baz'lik "delesyon" segmenti supheli goruldu (gercekci
CNV boyutlari genelde bin-milyon baz araliginda olur, 30 milyon baz
degil). Iki katmanli dogrulama yapildi:

### 1. IGV gorsel inceleme
ERBB2 bolgesinde (chr17:39,687,914-39,730,426) coverage cok dusuk
(9-22 okuma) ve dengesiz gorundu.

### 2. Sayisal derinlik karsilastirmasi (samtools depth)
```bash
samtools depth -r chr17:39687914-39730426 tumor.bam   # ort. derinlik: 24.51
samtools depth -r chr17:39687914-39730426 normal.bam  # ort. derinlik: 24.40
```

**Sonuc: Tumor ve normal derinlikleri neredeyse ozdes (fark <%0.5).**
ERBB2'de gercekte hicbir kopya sayisi farki yok - CNVkit'in bulgusu
**yanlis pozitif**.

## Kök Neden

Veri **exome** (hedeflenmis) olmasina ragmen CNVkit `--method wgs`
(whole genome, hedefsiz) modunda calistirildi. Bu uyumsuzluk, exome
capture'in dogal olarak "hedeflenmemis" biraktigi bolgelerdeki dusuk
coverage'i CNVkit'in yanlislikla "delesyon" olarak yorumlamasina
neden oldu.

**Dogru yaklasim:** Exome verisi icin CNVkit `--method hybrid`
(hedef BED dosyasiyla) veya `--method amplicon` kullanilmali.

## Öğrenilen Ders

Bir bioinformatik aracinin ciktisini, veri turune (WGS/exome/panel)
uygun modda calistirmadan kabul etmek ciddi yanlis pozitiflere yol
acabilir. Klinik onemi yuksek bir gende (ERBB2/HER2) boyle bir hata,
gercek bir klinik raporda yanlis bir tedavi kararina yol acabilirdi.
Sonuc kabul edilmeden once (a) biyolojik olarak makul olup olmadigi
sorgulanmali, (b) mumkunse bagimsiz bir yontemle (samtools depth gibi)
sayisal olarak dogrulanmalidir.

## Kullanılan Komutlar

```bash
# CNVkit (WGS modu - hatali sonuc verdi, ogrenme amacli tutuldu)
cnvkit.py batch tumor.bam --normal normal.bam --fasta chr17.fa \
  --annotate refFlat.txt --output-dir cnvkit_output --method wgs

# Dogrulama
samtools depth -r chr17:39687914-39730426 tumor.bam | \
  awk '{sum+=$3; count++} END {print sum/count}'
samtools depth -r chr17:39687914-39730426 normal.bam | \
  awk '{sum+=$3; count++} END {print sum/count}'
```

## Çıktı Dosyaları

- `results/tumor.call.cns` - CNVkit segment ciktisi (gen isimleriyle)
