import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

print(f"PyTorch versiyonu: {torch.__version__}")
print(f"MPS (Apple GPU) kullanılabilir mi: {torch.backends.mps.is_available()}")

# --- Küçük, CPU/M1'de rahatça çalışabilecek bir model seçiyoruz ---
# distilgpt2: GPT-2'nin küçültülmüş hali, ~82 milyon parametre
# (gerçek üretim modelleri milyarlarca parametre - bu sadece ÖĞRENME amaçlı)
MODEL_ADI = "distilgpt2"

print(f"\n{MODEL_ADI} modeli indiriliyor/yükleniyor...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_ADI)
model = AutoModelForCausalLM.from_pretrained(MODEL_ADI)

parametre_sayisi = sum(p.numel() for p in model.parameters())
print(f"\nModel yüklendi: {MODEL_ADI}")
print(f"Toplam parametre sayısı: {parametre_sayisi:,}")

# --- Fine-tune ETMEDEN ÖNCE, modelin klinik bir soruya nasıl cevap verdiğini görelim ---
prompt = "Hasta raporu: TP53 geninde"
girdi = tokenizer(prompt, return_tensors="pt")

print(f"\n=== Fine-tune ÖNCESİ, prompt: '{prompt}' ===")
with torch.no_grad():
    cikti = model.generate(
        **girdi,
        max_new_tokens=40,
        do_sample=True,
        temperature=0.8,
        pad_token_id=tokenizer.eos_token_id
    )
print(tokenizer.decode(cikti[0], skip_special_tokens=True))

print("""
GÖZLEM: Bu model (distilgpt2), genel İngilizce metinler üzerinde eğitildi -
klinik/genetik rapor formatını hiç görmedi. Çıktısı muhtemelen alakasız
veya tutarsız olacak. Bir sonraki adımda, bu modeli SENİN klinik rapor
formatına (Hafta 15'teki persona örnekleri) LoRA ile uyarlayacağız ve
aynı prompt'a nasıl farklı cevap verdiğini göreceğiz.
""")