import torch
import torch.nn as nn

print(f"PyTorch versiyonu: {torch.__version__}")
print(f"MPS (Apple Silicon GPU) kullanılabilir mi: {torch.backends.mps.is_available()}")

# --- 1. Tensor nedir? (PyTorch'un temel veri yapısı) ---
ornek_varyant = torch.tensor([0.977, 137.4, 8.5])
print(f"\nÖrnek varyant tensörü: {ornek_varyant}")
print(f"Tensör şekli (shape): {ornek_varyant.shape}")
print(f"Tensör veri tipi: {ornek_varyant.dtype}")

# --- 2. Birden fazla varyantı aynı anda temsil etme (batch) ---
varyant_batch = torch.tensor([
    [0.977, 137.4, 8.5],
    [0.120, 45.2, 1.2],
    [0.850, 190.0, 9.1],
])
print(f"\n3 varyantlık batch şekli: {varyant_batch.shape}")

# --- 3. En basit sinir ağı katmanı: Linear (doğrusal dönüşüm) ---
katman = nn.Linear(in_features=3, out_features=1)
print(f"\nKatmanın ağırlıkları (weights): {katman.weight}")
print(f"Katmanın bias'ı: {katman.bias}")

# --- 4. Bu katmandan veriyi geçirme (henüz eğitilmemiş, rastgele ağırlıklarla) ---
cikti = katman(varyant_batch)
print(f"\nEğitilmemiş modelin ham çıktısı:\n{cikti}")

# --- 5. Sigmoid ile çıktıyı 0-1 arasına sıkıştırma ---
sigmoid = nn.Sigmoid()
olasiliklar = sigmoid(cikti)
print(f"\nSigmoid sonrası (0-1 arası 'patojenite olasılığı'):\n{olasiliklar}")