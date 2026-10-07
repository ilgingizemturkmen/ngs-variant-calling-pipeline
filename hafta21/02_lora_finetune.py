import random
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model

random.seed(0)
torch.manual_seed(0)

MODEL_ADI = "distilgpt2"
tokenizer = AutoTokenizer.from_pretrained(MODEL_ADI)
tokenizer.pad_token = tokenizer.eos_token  # GPT-2'nin ayrı bir pad token'ı yok
model = AutoModelForCausalLM.from_pretrained(MODEL_ADI)

# =========================================================
# BÖLÜM 1: Sentetik "rapor formatı" eğitim verisi
# =========================================================
# ÖNEMLİ: Bu veri, modele BİÇİM (format) öğretmek için üretildi.
# İçindeki gen/varyant/sınıflandırma kombinasyonları klinik gerçek DEĞİL,
# model bu verilerden klinik doğru bilgi öğrenmeyecek, sadece biçimi taklit edecek.
genler = ["TP53", "BRCA1", "BRCA2", "EGFR", "KRAS", "PTEN", "ATM", "CHEK2"]
varyantlar = ["c.524G>A", "c.68_69del", "c.5946del", "c.2573T>G", "c.35G>A", "c.1A>G", "c.1100del"]
siniflar = ["Pathogenic", "Likely pathogenic", "Uncertain significance", "Likely benign", "Benign"]
oneriler = {
    "Pathogenic": "Refer for genetic counseling.",
    "Likely pathogenic": "Refer for genetic counseling.",
    "Uncertain significance": "Re-evaluate periodically.",
    "Likely benign": "No action required.",
    "Benign": "No action required.",
}

egitim_metinleri = []
for _ in range(60):
    g = random.choice(genler)
    v = random.choice(varyantlar)
    s = random.choice(siniflar)
    egitim_metinleri.append(
        f"REPORT | Gene: {g} | Variant: {v} | Classification: {s} | Recommendation: {oneriler[s]}"
        + tokenizer.eos_token
    )
print(f"Eğitim verisi: {len(egitim_metinleri)} örnek")
print(f"Örnek: {egitim_metinleri[0]}\n")

# =========================================================
# BÖLÜM 2: Fine-tune ÖNCESİ çıktı (adil karşılaştırma için İNGİLİZCE prompt)
# =========================================================
prompt = "REPORT | Gene: TP53 | Variant: c.524G>A | Classification:"

def uret(m, metin):
    girdi = tokenizer(metin, return_tensors="pt")
    with torch.no_grad():
        cikti = m.generate(**girdi, max_new_tokens=25, do_sample=False,
                           pad_token_id=tokenizer.eos_token_id)
    return tokenizer.decode(cikti[0], skip_special_tokens=True)

print("=== Fine-tune ÖNCESİ ===")
print(uret(model, prompt))

# =========================================================
# BÖLÜM 3: LoRA adaptörü ekle
# =========================================================
lora_ayari = LoraConfig(
    r=8,                          # adaptör matrislerinin "rank"ı (boyutu) - küçük = az parametre
    lora_alpha=16,                # ölçekleme katsayısı
    target_modules=["c_attn"],    # GPT-2'de dikkat (attention) katmanı
    lora_dropout=0.05,
    fan_in_fan_out=True,          # GPT-2'nin Conv1D katmanları için gerekli
    task_type="CAUSAL_LM",
)
model = get_peft_model(model, lora_ayari)
print("\n=== LoRA sonrası eğitilebilir parametre durumu ===")
model.print_trainable_parameters()

# =========================================================
# BÖLÜM 4: Eğitim döngüsü
# =========================================================
optimizer = torch.optim.AdamW(
    [p for p in model.parameters() if p.requires_grad], lr=5e-4
)

BATCH = 8
EPOCH = 15
model.train()
print("\nEğitim başlıyor...")
for epoch in range(1, EPOCH + 1):
    random.shuffle(egitim_metinleri)
    toplam_loss, adim = 0.0, 0
    for i in range(0, len(egitim_metinleri), BATCH):
        parti = egitim_metinleri[i:i + BATCH]
        girdi = tokenizer(parti, return_tensors="pt", padding=True)
        etiketler = girdi["input_ids"].clone()
        etiketler[girdi["attention_mask"] == 0] = -100  # padding kısımlarını loss'tan çıkar

        cikti = model(**girdi, labels=etiketler)
        cikti.loss.backward()
        optimizer.step()
        optimizer.zero_grad()
        toplam_loss += cikti.loss.item()
        adim += 1
    if epoch % 3 == 0:
        print(f"Epoch {epoch:2d} | Ortalama loss: {toplam_loss / adim:.4f}")

# =========================================================
# BÖLÜM 5: Fine-tune SONRASI çıktı
# =========================================================
model.eval()
print("\n=== Fine-tune SONRASI (aynı prompt) ===")
print(uret(model, prompt))

print("""
ÖNEMLİ UYARI:
Model artık rapor BİÇİMİNİ taklit edebiliyor olabilir, ama eğitim verisindeki
gen/varyant/sınıf eşleşmeleri rastgele üretildi. Modelin ürettiği
'Classification' değeri KLİNİK OLARAK DOĞRU olmak zorunda DEĞİL - sadece
biçime uygun. Fine-tuning biçim/üslup öğretir, doğru tıbbi bilgi garanti etmez.
""")

model.save_pretrained("lora_adaptor")