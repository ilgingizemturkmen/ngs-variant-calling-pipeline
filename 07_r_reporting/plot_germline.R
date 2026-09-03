library(vcfR)

vcf_path <- "data/nextflow_results/03_germline_variants/NA12878.vcf.gz"
vcf <- read.vcfR(vcf_path)

cat("Toplam varyant sayisi:", nrow(vcf@fix), "\n")

fix_df <- as.data.frame(vcf@fix)
fix_df$QUAL <- as.numeric(fix_df$QUAL)

fix_df$var_type <- ifelse(nchar(fix_df$REF) == 1 & nchar(fix_df$ALT) == 1, "SNP", "INDEL")

png("07_r_reporting/germline_variant_types.png", width = 800, height = 600)
barplot(table(fix_df$var_type),
        main = "NA12878 Germline Varyant Tipleri (chr17)",
        col = c("steelblue", "coral"),
        ylab = "Varyant Sayisi")
dev.off()

png("07_r_reporting/germline_quality_dist.png", width = 800, height = 600)
hist(fix_df$QUAL,
     main = "NA12878 Germline Varyant Kalite Skoru Dagilimi",
     xlab = "QUAL Skoru",
     col = "lightgreen",
     breaks = 20)
dev.off()

cat("Grafikler kaydedildi.\n")
