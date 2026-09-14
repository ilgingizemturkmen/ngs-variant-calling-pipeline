import torch
import torch.nn as nn
import random

random.seed(42)
torch.manual_seed(42)

# --- 1. Sentetik varyant veri seti üret ---
# Özellikler: [AF (alel frekansı), kalite_skoru, konservasyon_skoru, gen_onem_skoru]
# Etiket: 1 = patojenik, 0 = benign
# Gerçekçi mantık: yüksek AF + yüksek kalite + yüksek konservasyon + önemli gen -> patojenik olasılığı artar

def varyant_uret(patojenik: bool):
    if patojenik:
        af = random.uniform(0.6, 1.0)
        kalite = random.uniform(100, 250)
        konservasyon = random.uniform(6, 10)
        gen_onem = random.uniform(0.7, 1.0)  # TP53, BRCA1 gibi kritik genler
    else:
        af = random.uniform(0.01, 0.5)
        kalite = random.uniform(10, 120)
        konservasyon = random.uniform(0, 5)
        gen_onem = random.uniform(0.0, 0.6)
    # Biraz gürültü ekleyerek gerçekçilik katıyoruz (gerçek veri hiçbir zaman kusursuz ayrışmaz)
    return [af + random.gauss(0, 0.05), kalite + random.gauss(0, 10),
            konservasyon + random.gauss(0, 0.5), gen_onem + random.gauss(0, 0.05)]

N = 2000  # toplam varyant sayısı
X_liste = []
y_liste = []
for _ in range(N):
    patojenik_mi = random.random() < 0.5  # %50 patojenik, %50 benign
    X_liste.append(varyant_uret(patojenik_mi))
    y_liste.append(1.0 if patojenik_mi else 0.0)

X = torch.tensor(X_liste, dtype=torch.float32)
y = torch.tensor(y_liste, dtype=torch.float32).unsqueeze(1)  # şekli (N,) -> (N,1) yapıyoruz

# --- Eğitim/test ayrımı (train/test split) ---
egitim_boyutu = int(0.8 * N)
X_egitim, X_test = X[:egitim_boyutu], X[egitim_boyutu:]
y_egitim, y_test = y[:egitim_boyutu], y[egitim_boyutu:]

print(f"Toplam varyant: {N}, Eğitim: {len(X_egitim)}, Test: {len(X_test)}")
print(f"Örnek özellik vektörü: {X[0]}")
print(f"Örnek etiket: {y[0]}\n")

# --- 2. Model mimarisi: birden fazla katmanlı basit bir sinir ağı (MLP) ---
class PatojeniteSiniflandirici(nn.Module):
    def __init__(self):
        super().__init__()
        self.katman1 = nn.Linear(4, 16)   # 4 özellik -> 16 gizli nöron
        self.aktivasyon1 = nn.ReLU()
        self.katman2 = nn.Linear(16, 8)   # 16 -> 8 gizli nöron
        self.aktivasyon2 = nn.ReLU()
        self.cikti_katmani = nn.Linear(8, 1)  # 8 -> 1 (patojenite skoru)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        x = self.aktivasyon1(self.katman1(x))
        x = self.aktivasyon2(self.katman2(x))
        x = self.sigmoid(self.cikti_katmani(x))
        return x

model = PatojeniteSiniflandirici()
print(f"Model mimarisi:\n{model}\n")

# --- 3. Loss function ve optimizer ---
loss_fn = nn.BCELoss()  # Binary Cross Entropy - ikili sınıflandırma için standart loss
optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

# --- 4. Eğitim döngüsü ---
epoch_sayisi = 100
print("Eğitim başlıyor...\n")
for epoch in range(1, epoch_sayisi + 1):
    model.train()

    # İleri geçiş (forward pass): modelden tahmin al
    tahminler = model(X_egitim)
    loss = loss_fn(tahminler, y_egitim)

    # Geri yayılım (backpropagation): hatayı ağırlıklara göre türevini al
    optimizer.zero_grad()  # önceki adımın gradyanlarını sıfırla
    loss.backward()        # gradyanları hesapla
    optimizer.step()       # ağırlıkları güncelle

    if epoch % 10 == 0:
        with torch.no_grad():
            test_tahminler = model(X_test)
            test_loss = loss_fn(test_tahminler, y_test)
            dogruluk = ((test_tahminler > 0.5).float() == y_test).float().mean()
        print(f"Epoch {epoch:3d} | Eğitim Loss: {loss.item():.4f} | Test Loss: {test_loss.item():.4f} | Test Doğruluk: {dogruluk.item()*100:.1f}%")

print("\nEğitim tamamlandı.")

# --- 5. Eğitilmiş modeli, Adım 1'deki örnek varyantlarla tekrar test edelim ---
print("\n=== Eğitilmiş model, örnek varyantlar üzerinde ===")
ornek_varyantlar = torch.tensor([
    [0.977, 137.4, 8.5, 0.9],   # TP53 R175H benzeri - PATOJENİK olmalı
    [0.120, 45.2, 1.2, 0.2],    # düşük her şey - BENİGN olmalı
    [0.850, 190.0, 9.1, 0.85],  # yüksek konservasyon - PATOJENİK olmalı
])
model.eval()
with torch.no_grad():
    sonuclar = model(ornek_varyantlar)
for i, sonuc in enumerate(sonuclar):
    tahmin = "PATOJENİK" if sonuc.item() > 0.5 else "BENİGN"
    print(f"Varyant {i+1}: olasılık={sonuc.item():.4f} -> {tahmin}")

# --- Modeli diske kaydet (ileride tekrar kullanmak için) ---
torch.save(model.state_dict(), "patojenite_modeli.pt")
print("\nModel 'patojenite_modeli.pt' olarak kaydedildi.")