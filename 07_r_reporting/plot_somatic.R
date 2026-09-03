library(vcfR)

vcf_path <- "data/nextflow_results/04_somatic_variants/somatic_filtered.vcf.gz"
vcf <- read.vcfR(vcf_path)

fix_df <- as.data.frame(vcf@fix)
pass_df <- fix_df[fix_df$FILTER == "PASS", ]

cat("Toplam aday varyant:", nrow(fix_df), "\n")
cat("PASS filtresini gecen varyant:", nrow(pass_df), "\n")

png("07_r_reporting/somatic_filter_summary.png", width = 800, height = 600)
filter_counts <- table(fix_df$FILTER == "PASS")
names(filter_counts) <- c("Filtrelendi", "PASS")
barplot(filter_counts,
        main = "Somatic Varyant Filtreleme Sonucu (Mutect2)",
        col = c("firebrick", "forestgreen"),
        ylab = "Varyant Sayisi")
dev.off()

extract_tlod <- function(info_str) {
  m <- regmatches(info_str, regexpr("TLOD=[0-9.eE+-]+", info_str))
  as.numeric(gsub("TLOD=", "", m))
}
pass_df$TLOD <- sapply(pass_df$INFO, extract_tlod)

tp53_pos <- which(pass_df$POS == "7675088")
cat("\nTP53 R175H (chr17:7675088) PASS listesinde bulundu mu:", length(tp53_pos) > 0, "\n")
cat("TLOD degeri:", pass_df$TLOD[tp53_pos], "\n")

png("07_r_reporting/somatic_tp53_highlight.png", width = 900, height = 600)
plot(as.numeric(pass_df$POS), pass_df$TLOD,
     main = "PASS Somatic Varyantlar - chr17 Pozisyonu vs TLOD",
     xlab = "Pozisyon (chr17)", ylab = "TLOD (Guven Skoru)",
     pch = 19, col = "gray60")
points(7675088, pass_df$TLOD[tp53_pos], pch = 19, col = "red", cex = 2)
text(7675088, pass_df$TLOD[tp53_pos], "TP53 R175H", pos = 3, col = "red", font = 2)
dev.off()

cat("\nGrafikler kaydedildi.\n")
