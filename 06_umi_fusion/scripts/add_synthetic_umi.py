#!/usr/bin/env python3
"""
Sentetik UMI ekleme scripti - EGITIM AMACLIDIR.
Gercek UMI verisi olmayan bir BAM dosyasina, okuma adina (query name)
dayali rastgele ama TUTARLI (ayni template icin ayni) UMI etiketleri
ekler. Bu, fgbio'nun UMI-based consensus pipeline'inin adimlarini
gostermek icindir - gercek bir hata duzeltmesi/klinik sonuc URETMEZ.
"""

import sys
import hashlib
import random

def generate_umi(read_name, length=8):
    h = hashlib.md5(read_name.encode()).hexdigest()
    random.seed(h)
    bases = "ACGT"
    return "".join(random.choice(bases) for _ in range(length))

for line in sys.stdin:
    if line.startswith("@"):
        sys.stdout.write(line)
        continue
    fields = line.rstrip("\n").split("\t")
    read_name = fields[0]
    umi = generate_umi(read_name)
    fields.append(f"RX:Z:{umi}")
    sys.stdout.write("\t".join(fields) + "\n")
