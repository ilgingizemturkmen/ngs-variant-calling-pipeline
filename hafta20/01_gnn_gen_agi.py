import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.data import Data
from torch_geometric.nn import GCNConv

torch.manual_seed(42)

# =========================================================
# BÖLÜM 1: Gen etkileşim ağını kurma (node = gen, edge = bilinen etkileşim)
# =========================================================

# 10 gen: TP53 ekseni + bazı bilinen onkogenler/tümör baskılayıcılar
genler = ["TP53", "MDM2", "ATM", "CHEK2", "BRCA1", "CDKN1A", "BAX", "EGFR", "KRAS", "PTEN"]
gen_index = {gen: i for i, gen in enumerate(genler)}

# Her genin 2 özelliği: [mutasyon_sikligi (0-1), ekspresyon_degisimi (-1 ile 1 arasi, log-fold-change benzeri)]
# Bu degerler TCGA'daki genel egilimlere kabaca benzer sekilde, ogrenme amacli elle verildi
ozellikler = torch.tensor([
    [0.90, -0.80],   # TP53: cok sik mutasyona ugrar, mutant oldugunda hedef genler baskilanir
    [0.15,  0.60],   # MDM2: TP53'u baskilar, WT TP53'te aktive olur
    [0.20,  0.10],   # ATM: DNA hasar yaniti
    [0.18,  0.05],   # CHEK2: DNA hasar yaniti
    [0.25, -0.20],   # BRCA1: tumor baskilayici
    [0.10, -0.70],   # CDKN1A (p21): TP53 hedefi, mutant TP53'te dusuk
    [0.08, -0.65],   # BAX: TP53 hedefi, apoptoz
    [0.35,  0.75],   # EGFR: onkogen, sik aktive mutasyon
    [0.40,  0.70],   # KRAS: onkogen, sik aktive mutasyon
    [0.22, -0.30],   # PTEN: tumor baskilayici
], dtype=torch.float)

# Kenarlar: bilinen biyolojik etkileşimler (STRING veritabanı tarzı, basitleştirilmiş)
# Çift yönlü olduğu için her bağlantıyı iki kez (A->B ve B->A) yazıyoruz
baglantilar = [
    ("TP53", "MDM2"), ("TP53", "ATM"), ("TP53", "CDKN1A"), ("TP53", "BAX"),
    ("ATM", "CHEK2"), ("TP53", "BRCA1"), ("EGFR", "KRAS"), ("KRAS", "PTEN"),
    ("PTEN", "TP53"), ("BRCA1", "ATM"),
]

kaynak, hedef = [], []
for a, b in baglantilar:
    kaynak += [gen_index[a], gen_index[b]]
    hedef += [gen_index[b], gen_index[a]]

edge_index = torch.tensor([kaynak, hedef], dtype=torch.long)

# Etiketler: 1 = bilinen kanser sürücü geni (driver), 0 = değil
# (Gerçek COSMIC Cancer Gene Census sınıflandırmasına kabaca dayanıyor)
etiketler = torch.tensor([1, 1, 1, 1, 1, 0, 0, 1, 1, 1], dtype=torch.long)

veri = Data(x=ozellikler, edge_index=edge_index, y=etiketler)
print("=== Graf özeti ===")
print(veri)
print(f"Node sayısı: {veri.num_nodes}, Kenar sayısı: {veri.num_edges}")

# =========================================================
# BÖLÜM 2: GCN (Graph Convolutional Network) modeli
# =========================================================

class GenGCN(nn.Module):
    def __init__(self, girdi_boyutu, gizli_boyut, cikti_boyutu):
        super().__init__()
        # GCNConv: her node'un özelliğini, KOMŞULARININ özellikleriyle harmanlayarak günceller
        self.katman1 = GCNConv(girdi_boyutu, gizli_boyut)
        self.katman2 = GCNConv(gizli_boyut, cikti_boyutu)

    def forward(self, x, edge_index):
        x = self.katman1(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=0.3, training=self.training)
        x = self.katman2(x, edge_index)
        return x

model = GenGCN(girdi_boyutu=2, gizli_boyut=8, cikti_boyutu=2)
optimizer = torch.optim.Adam(model.parameters(), lr=0.05, weight_decay=5e-4)

print(f"\nModel mimarisi:\n{model}")

# =========================================================
# BÖLÜM 3: Eğitim döngüsü (tüm 10 gen üzerinde - küçük graf olduğu için train/test ayırmıyoruz,
# ama bunun bir sınırlılık olduğunu NOT ediyoruz)
# =========================================================

print("\nEğitim başlıyor...\n")
model.train()
for epoch in range(1, 201):
    optimizer.zero_grad()
    cikti = model(veri.x, veri.edge_index)
    loss = F.cross_entropy(cikti, veri.y)
    loss.backward()
    optimizer.step()

    if epoch % 40 == 0:
        model.eval()
        with torch.no_grad():
            tahminler = model(veri.x, veri.edge_index).argmax(dim=1)
            dogruluk = (tahminler == veri.y).float().mean()
        print(f"Epoch {epoch:3d} | Loss: {loss.item():.4f} | Doğruluk: {dogruluk.item()*100:.1f}%")
        model.train()

# =========================================================
# BÖLÜM 4: Sonuçları yorumlama
# =========================================================
print("\n=== Her gen için model tahmini ===")
model.eval()
with torch.no_grad():
    olasiliklar = F.softmax(model(veri.x, veri.edge_index), dim=1)
    tahminler = olasiliklar.argmax(dim=1)

for i, gen in enumerate(genler):
    tahmin = "DRIVER" if tahminler[i] == 1 else "DEĞİL"
    gercek = "DRIVER" if etiketler[i] == 1 else "DEĞİL"
    dogru_mu = "✓" if tahminler[i] == etiketler[i] else "✗ YANLIŞ"
    print(f"{gen:8s} | Gerçek: {gercek:7s} | Tahmin: {tahmin:7s} (olasılık={olasiliklar[i][1]:.3f}) | {dogru_mu}")

print("""
ÖNEMLİ METODOLOJİK NOT:
Bu model, 10 node'luk MİNİK bir graf üzerinde, train/test ayrımı yapmadan
(tüm veri hem eğitim hem değerlendirme için kullanıldı) eğitildi. Bu,
GERÇEK bir araştırmada KABUL EDİLEMEZ bir pratiktir (overfitting riski
çok yüksek, "doğruluk" rakamı güvenilir değildir). Amaç, GCN katmanının
NASIL çalıştığını (komşu bilgisini nasıl topladığını) göstermektir -
gerçek bir GNN projesi, STRING/BioGRID'den binlerce node'luk gerçek bir
etkileşim ağı ve uygun train/validation/test ayrımı gerektirir.
""")