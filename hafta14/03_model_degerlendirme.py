import torch
import torch.nn as nn
import random
from sklearn.metrics import confusion_matrix, precision_score, recall_score, f1_score

random.seed(42)
torch.manual_seed(42)

# --- Aynı veri üretim mantığı (önceki script ile birebir aynı olmalı, tutarlılık için) ---
def varyant_uret(patojenik: bool):
    if patojenik:
        af = random.uniform(0.6, 1.0)
        kalite = random.uniform(100, 250)
        konservasyon = random.uniform(6, 10)
        gen_onem = random.uniform(0.7, 1.0)
    else:
        af = random.uniform(0.01, 0.5)
        kalite = random.uniform(10, 120)
        konservasyon = random.uniform(0, 5)
        gen_onem = random.uniform(0.0, 0.6)
    return [af + random.gauss(0, 0.05), kalite + random.gauss(0, 10),
            konservasyon + random.gauss(0, 0.5), gen_onem + random.gauss(0, 0.05)]

N = 2000
X_liste, y_liste = [], []
for _ in range(N):
    patojenik_mi = random.random() < 0.5
    X_liste.append(varyant_uret(patojenik_mi))
    y_liste.append(1.0 if patojenik_mi else 0.0)

X = torch.tensor(X_liste, dtype=torch.float32)
y = torch.tensor(y_liste, dtype=torch.float32).unsqueeze(1)

egitim_boyutu = int(0.8 * N)
X_egitim, X_test = X[:egitim_boyutu], X[egitim_boyutu:]
y_egitim, y_test = y[:egitim_boyutu], y[egitim_boyutu:]

# --- Aynı model mimarisi ---
class PatojeniteSiniflandirici(nn.Module):
    def __init__(self):
        super().__init__()
        self.katman1 = nn.Linear(4, 16)
        self.aktivasyon1 = nn.ReLU()
        self.katman2 = nn.Linear(16, 8)
        self.aktivasyon2 = nn.ReLU()
        self.cikti_katmani = nn.Linear(8, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        x = self.aktivasyon1(self.katman1(x))
        x = self.aktivasyon2(self.katman2(x))
        x = self.sigmoid(self.cikti_katmani(x))
        return x

# --- Kaydedilmiş modeli yüklüyoruz (yeniden eğitmeye gerek yok) ---
model = PatojeniteSiniflandirici()
model.load_state_dict(torch.load("patojenite_modeli.pt"))
model.eval()
print("Kaydedilmiş model yüklendi.\n")

# --- Test seti üzerinde tahmin üret ---
with torch.no_grad():
    test_olasiliklar = model(X_test)
    test_tahminler = (test_olasiliklar > 0.5).float()

# --- sklearn metrikleri için tensor'ları normal Python listelerine çeviriyoruz ---
gercek = y_test.numpy().flatten()
tahmin = test_tahminler.numpy().flatten()

print("=" * 60)
print("CONFUSION MATRIX (Karışıklık Matrisi)")
print("=" * 60)
cm = confusion_matrix(gercek, tahmin)
print(f"                  Tahmin: BENİGN   Tahmin: PATOJENİK")
print(f"Gerçek: BENİGN         {cm[0][0]:^6}          {cm[0][1]:^6}")
print(f"Gerçek: PATOJENİK      {cm[1][0]:^6}          {cm[1][1]:^6}")

tn, fp, fn, tp = cm.ravel()
print(f"\nTrue Negative (doğru BENİGN):     {tn}")
print(f"False Positive (yanlış PATOJENİK): {fp}  <- gereksiz endişe/tetkik")
print(f"False Negative (KAÇIRILAN patojenik): {fn}  <- EN TEHLİKELİ HATA")
print(f"True Positive (doğru PATOJENİK):  {tp}")

print("\n" + "=" * 60)
print("METRİKLER")
print("=" * 60)
precision = precision_score(gercek, tahmin)
recall = recall_score(gercek, tahmin)
f1 = f1_score(gercek, tahmin)
dogruluk = (tahmin == gercek).mean()

print(f"Doğruluk (Accuracy):  {dogruluk*100:.1f}%")
print(f"Precision:            {precision*100:.1f}%  (patojenik dediklerimin yüzde kaçı gerçekten patojenik)")
print(f"Recall (Duyarlılık):  {recall*100:.1f}%  (gerçek patojeniklerin yüzde kaçını yakaladık)")
print(f"F1 Score:             {f1*100:.1f}%  (precision ve recall'un dengeli ortalaması)")

print("\n" + "=" * 60)
print("KLİNİK YORUM")
print("=" * 60)
if fn > 0:
    print(f"UYARI: {fn} patojenik varyant 'benign' olarak yanlış sınıflandırıldı.")
    print("Klinik kullanımda bu, gerçek bir hastalığa neden olan mutasyonun")
    print("gözden kaçırılması anlamına gelir - bu tür modeller ASLA tek başına")
    print("klinik karar vermek için kullanılmamalı, uzman doğrulaması şarttır.")
else:
    print("Bu test setinde hiç patojenik varyant kaçırılmadı (False Negative = 0).")
    print("Ancak gerçek klinik veride bu her zaman garanti edilemez.")