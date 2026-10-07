import re
import random
from collections import Counter
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

random.seed(1)
MODEL_ADI = "distilgpt2"
tokenizer = AutoTokenizer.from_pretrained(MODEL_ADI)
temel = AutoModelForCausalLM.from_pretrained(MODEL_ADI)
model = PeftModel.from_pretrained(temel, "lora_adaptor")
model.eval()

oneriler = {
    "Pathogenic": "Refer for genetic counseling.",
    "Likely pathogenic": "Refer for genetic counseling.",
    "Uncertain significance": "Re-evaluate periodically.",
    "Likely benign": "No action required.",
    "Benign": "No action required.",
}

# Biçim kontrolü: çıktı satırının tamamı bu kalıba uymalı
kalip = re.compile(
    r"REPORT \| Gene: \S+ \| Variant: \S+ \| Classification: "
    r"(Pathogenic|Likely pathogenic|Uncertain significance|Likely benign|Benign)"
    r" \| Recommendation: (.+)"
)

def uret(metin):
    girdi = tokenizer(metin, return_tensors="pt")
    with torch.no_grad():
        cikti = model.generate(**girdi, max_new_tokens=30, do_sample=False,
                               pad_token_id=tokenizer.eos_token_id)
    return tokenizer.decode(cikti[0], skip_special_tokens=True).split("\n")[0].strip()

def degerlendir(prompts, adaptor_acik):
    uyumlu, tutarli = 0, 0
    siniflar = Counter()
    ornekler = []
    for p in prompts:
        if adaptor_acik:
            cikti = uret(p)
        else:
            with model.disable_adapter():   # LoRA'yı geçici kapat = taban model
                cikti = uret(p)
        e = kalip.fullmatch(cikti)
        if e:
            uyumlu += 1
            siniflar[e.group(1)] += 1
            if oneriler[e.group(1)] == e.group(2).strip():
                tutarli += 1
        ornekler.append(cikti)
    return uyumlu, tutarli, siniflar, ornekler

gorulen_genler = ["TP53", "BRCA1", "BRCA2", "EGFR", "KRAS", "PTEN", "ATM", "CHEK2"]
gorulen_var = ["c.524G>A", "c.68_69del", "c.5946del", "c.2573T>G", "c.35G>A", "c.1A>G", "c.1100del"]
gorulmeyen_genler = ["MLH1", "APC", "RET", "VHL"]
yeni_var = ["c.1234A>G", "c.77del"]

def prompt_yap(g, v):
    return f"REPORT | Gene: {g} | Variant: {v} | Classification:"

gruplar = {
    "Eğitimde görülen gen/varyantlar": [prompt_yap(random.choice(gorulen_genler), random.choice(gorulen_var)) for _ in range(20)],
    "Eğitimde HİÇ görülmeyen gen/varyantlar": [prompt_yap(random.choice(gorulmeyen_genler), random.choice(yeni_var)) for _ in range(20)],
}

for grup_adi, prompts in gruplar.items():
    print("=" * 60)
    print(grup_adi)
    print("=" * 60)
    for ad, acik in [("TABAN model", False), ("LoRA fine-tune", True)]:
        u, t, s, ornek = degerlendir(prompts, acik)
        print(f"\n{ad}: biçime uyan {u}/20 | sınıf-öneri tutarlı {t}/{u}")
        if s:
            print(f"  Üretilen sınıf dağılımı: {dict(s)}")
        print(f"  Örnek çıktı: {ornek[0]}")

print("""
YORUM İÇİN NOT:
- 'Görülen' grup gerçek bir held-out test DEĞİL: 56 olası gen/varyant kombinasyonu
  var, eğitimde 60 örnek kullanıldı, bazıları birebir tekrar etmiş olabilir.
- Sınıf dağılımı tek bir sınıfa yığılıyorsa, model gen/varyanta bakmıyor demektir.
""")