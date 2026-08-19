#!/usr/bin/env Rscript
# Hafta 4: GATK4 vs DeepVariant - Venn Diagram Karsilastirmasi

if (!requireNamespace("VennDiagram", quietly = TRUE)) {
  install.packages("VennDiagram", repos = "https://cloud.r-project.org")
}
library(VennDiagram)

sadece_gatk4 <- 3
sadece_deepvariant <- 15
ortak <- 51

gatk4_toplam <- sadece_gatk4 + ortak
deepvariant_toplam <- sadece_deepvariant + ortak

venn.plot <- draw.pairwise.venn(
  area1 = gatk4_toplam,
  area2 = deepvariant_toplam,
  cross.area = ortak,
  category = c(paste0("GATK4\n(n=", gatk4_toplam, ")"),
               paste0("DeepVariant\n(n=", deepvariant_toplam, ")")),
  fill = c("#4C72B0", "#DD8452"),
  alpha = 0.6,
  cex = 1.5,
  cat.cex = 1.3,
  cat.pos = c(-30, 30),
  scaled = TRUE,
  euler.d = TRUE
)

png("results/gatk4_vs_deepvariant_venn.png", width = 800, height = 800, res = 150)
grid::grid.draw(venn.plot)
dev.off()

cat("Venn diyagrami kaydedildi.\n")
cat("Sadece GATK4:", sadece_gatk4, "\n")
cat("Sadece DeepVariant:", sadece_deepvariant, "\n")
cat("Ortak:", ortak, "\n")
cat("Uyum orani (Jaccard):", round(ortak / (sadece_gatk4 + sadece_deepvariant + ortak), 3), "\n")
