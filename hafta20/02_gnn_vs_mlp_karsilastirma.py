import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.data import Data
from torch_geometric.nn import GCNConv

torch.manual_seed(42)

# --- Aynı veri (01_gnn_gen_agi.py'den birebir aynı) ---
genler = ["TP53", "MDM2", "ATM", "CHEK2", "BRCA1", "CDKN1A", "BAX", "EGFR", "KRAS", "PTEN"]
gen_index = {gen: i for i, gen in enumerate(genler)}

ozellikler = torch.tensor([
    [0.90, -0.80], [0.15, 0.60], [0.20, 0.10], [0.18, 0.05], [0.25, -0.20],
    [0.10, -0.70], [0.08, -0.65], [0.35, 0.75], [0.40, 0.70], [0.22, -0.30],
], dtype=torch.float)

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
etiketler = torch.tensor([1, 1, 1, 1, 1, 0, 0, 1, 1, 1], dtype=torch.long)

veri = Data(x=ozellikler, edge_index=edge_index, y=etiketler)

# =========================================================
# MODEL 1: GCN (komsuluk bilgisi KULLANIR)
# =========================================================
class GenGCN(nn.Module):
    def __init__(self):
        super().__init__()
        self.katman1 = GCNConv(2, 8)
        self.katman2 = GCNConv(8, 2)
    def forward(self, x, edge_index):
        x = F.relu(self.katman1(x, edge_index))
        x = F.dropout(x, p=0.3, training=self.training)
        return self.katman2(x, edge_index)

# =========================================================
# MODEL 2: Duz MLP (komsuluk bilgisi KULLANMAZ - sadece kendi ozellikleri)
# =========================================================
class GenMLP(nn.Module):
    def __init__(self):
        super().__init__()
        self.katman1 = nn.Linear(2, 8)
        self.katman2 = nn.Linear(8, 2)
    def forward(self, x, edge_index=None):  # edge_index'i kabul eder ama HIC KULLANMAZ
        x = F.relu(self.katman1(x))
        x = F.dropout(x, p=0.3, training=self.training)
        return self.katman2(x)

def egit_ve_degerlendir(model, isim):
    optimizer = torch.optim.Adam(model.parameters(), lr=0.05, weight_decay=5e-4)
    model.train()
    for epoch in range(200):
        optimizer.zero_grad()
        cikti = model(veri.x, veri.edge_index)
        loss = F.cross_entropy(cikti, veri.y)
        loss.backward()
        optimizer.step()

    model.eval()
    with torch.no_grad():
        olasiliklar = F.softmax(model(veri.x, veri.edge_index), dim=1)
        tahminler = olasiliklar.argmax(dim=1)
        dogruluk = (tahminler == veri.y).float().mean()

    print(f"\n=== {isim} ===")
    print(f"Son loss: {loss.item():.4f} | Doğruluk: {dogruluk.item()*100:.1f}%")
    for i, gen in enumerate(genler):
        tahmin = "DRIVER" if tahminler[i] == 1 else "DEĞİL"
        print(f"  {gen:8s} | olasılık={olasiliklar[i][1]:.3f} | tahmin={tahmin}")
    return dogruluk.item(), olasiliklar[:, 1].tolist()

# --- İki modeli de aynı veriyle eğit ---
gcn_dogruluk, gcn_olasiliklar = egit_ve_degerlendir(GenGCN(), "GCN (komşuluk bilgisi İLE)")
mlp_dogruluk, mlp_olasiliklar = egit_ve_degerlendir(GenMLP(), "MLP (komşuluk bilgisi OLMADAN)")

print("\n" + "=" * 60)
print("KARŞILAŞTIRMA SONUCU")
print("=" * 60)
print(f"GCN doğruluk: {gcn_dogruluk*100:.1f}%")
print(f"MLP doğruluk: {mlp_dogruluk*100:.1f}%")

if abs(gcn_dogruluk - mlp_dogruluk) < 0.01:
    print("""
SONUÇ: İki model de aynı doğruluğa ulaştı. Bu, mevcut veri setinde
(sadece mutasyon sıklığı + ekspresyon değişimi, 10 node) komşuluk
bilgisinin EKSTRA bir ayırt edici güç KATMADIĞINI gösteriyor - çünkü
node'ların kendi özellikleri zaten sınıfları net şekilde ayırıyor.
GNN'in gerçek avantajı, node özelliklerinin TEK BAŞINA yetersiz kaldığı,
komşuluk yapısının belirleyici olduğu durumlarda ortaya çıkar.
""")
else:
    print(f"""
SONUÇ: Modeller farklı performans gösterdi (fark: {abs(gcn_dogruluk-mlp_dogruluk)*100:.1f} puan).
Bu, komşuluk bilgisinin bu veri setinde gerçekten bir fark yarattığına
işaret ediyor.
""")