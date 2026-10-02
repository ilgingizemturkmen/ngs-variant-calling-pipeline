import torch
import torch.nn.functional as F
from torch_geometric.data import Data
from torch_geometric.nn import GCNConv
import random

random.seed(5)
torch.manual_seed(5)

# --- Hesaplar: 15 normal, 5 dolandirici (ring - birbirine yogun baglanti), 1 "gizlenmis" dolandirici ---
isimler = [f"Hesap_{i}" for i in range(21)]
# 0-14: normal, 15-19: acik dolandirici ring, 20: GIZLENMIS dolandirici (normal gorunumlu ama ring'e bagli)

ozellikler = []
etiketler = []
for i in range(21):
    if i < 15:  # normal
        ozellikler.append([random.uniform(1,5), random.uniform(50,200)])  # [islem_sayisi, ort_tutar]
        etiketler.append(0)
    elif i < 20:  # acik dolandirici: cok fazla, kucuk tutarli islem (tipik ring paterni)
        ozellikler.append([random.uniform(20,40), random.uniform(10,30)])
        etiketler.append(1)
    else:  # GIZLENMIS dolandirici: ozellikleri NORMAL gorunuyor!
        ozellikler.append([random.uniform(1,5), random.uniform(50,200)])  # normal gibi gorunen ozellikler
        etiketler.append(1)  # ama GERCEKTE dolandirici

ozellikler = torch.tensor(ozellikler, dtype=torch.float)
etiketler = torch.tensor(etiketler, dtype=torch.long)

# --- Baglantilar: dolandirici ring (15-19) birbirine yogun bagli, gizlenmis hesap (20) RING'E bagli ---
kaynak, hedef = [], []
ring_uyeleri = list(range(15, 20))
for a in ring_uyeleri:
    for b in ring_uyeleri:
        if a != b:
            kaynak.append(a); hedef.append(b)
# Gizlenmis hesap (20), ring'in 2 uyesiyle baglantili - TEK ipucu bu baglanti
for ring_uyesi in [15, 17]:
    kaynak += [20, ring_uyesi]; hedef += [ring_uyesi, 20]
# Normal hesaplar da kendi aralarinda biraz baglantili (gercekci olsun diye)
for _ in range(15):
    a, b = random.sample(range(15), 2)
    kaynak += [a, b]; hedef += [b, a]

edge_index = torch.tensor([kaynak, hedef], dtype=torch.long)
veri = Data(x=ozellikler, edge_index=edge_index, y=etiketler)

class HesapGCN(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.k1 = GCNConv(2, 8); self.k2 = GCNConv(8, 2)
    def forward(self, x, edge_index):
        x = F.relu(self.k1(x, edge_index))
        return self.k2(x, edge_index)

class HesapMLP(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.k1 = torch.nn.Linear(2, 8); self.k2 = torch.nn.Linear(8, 2)
    def forward(self, x, edge_index=None):
        x = F.relu(self.k1(x))
        return self.k2(x)

def egit(model, isim):
    opt = torch.optim.Adam(model.parameters(), lr=0.05, weight_decay=1e-3)
    for _ in range(200):
        model.train(); opt.zero_grad()
        loss = F.cross_entropy(model(veri.x, veri.edge_index), veri.y)
        loss.backward(); opt.step()
    model.eval()
    with torch.no_grad():
        tahmin = model(veri.x, veri.edge_index).argmax(dim=1)
    print(f"\n=== {isim} ===")
    print(f"'Gizlenmiş' hesap (index 20) tahmini: {'DOLANDIRICI' if tahmin[20]==1 else 'NORMAL (KAÇIRILDI!)'}")
    print(f"Genel doğruluk: {(tahmin==veri.y).float().mean().item()*100:.1f}%")

egit(HesapGCN(), "GCN (komşuluk bilgisi İLE)")
egit(HesapMLP(), "MLP (komşuluk bilgisi OLMADAN)")