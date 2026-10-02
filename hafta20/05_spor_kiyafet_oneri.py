import torch
import torch.nn.functional as F
from torch_geometric.data import Data
from torch_geometric.nn import GCNConv
from torch_geometric.utils import negative_sampling

torch.manual_seed(1)

kullanicilar = ["Ayse", "Mehmet", "Fatma", "Can", "Zeynep", "Burak"]
urunler = ["Tayt", "Spor_Sutyeni", "Ceket", "Corap", "Gozluk",
           "Sapka", "Ayakkabi", "Canta", "Spor_Cantasi", "Boyunluk"]

tum_node = kullanicilar + urunler
idx = {n: i for i, n in enumerate(tum_node)}
n_kullanici, n_urun = len(kullanicilar), len(urunler)

# Ozellik: [tip (0=kullanici, 1=urun), rastgele bir "ozellik" (basitlik icin)]
ozellikler = torch.zeros(len(tum_node), 2)
ozellikler[:n_kullanici, 0] = 0
ozellikler[n_kullanici:, 0] = 1
ozellikler[:, 1] = torch.rand(len(tum_node))

# --- Satin alma gecmisi (egitim verisi - "pozitif" baglantilar) ---
satin_almalar = [
    ("Ayse","Tayt"), ("Ayse","Spor_Sutyeni"), ("Ayse","Corap"),
    ("Mehmet","Ayakkabi"), ("Mehmet","Corap"), ("Mehmet","Sapka"),
    ("Fatma","Tayt"), ("Fatma","Gozluk"), ("Fatma","Spor_Cantasi"),
    ("Can","Ceket"), ("Can","Boyunluk"), ("Can","Sapka"),
    ("Zeynep","Spor_Sutyeni"), ("Zeynep","Tayt"), ("Zeynep","Canta"),
    ("Burak","Ayakkabi"), ("Burak","Ceket"), ("Burak","Corap"),
]
kaynak, hedef = [], []
for a, b in satin_almalar:
    kaynak += [idx[a], idx[b]]; hedef += [idx[b], idx[a]]
edge_index = torch.tensor([kaynak, hedef], dtype=torch.long)
veri = Data(x=ozellikler, edge_index=edge_index)

class OneriGCN(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.k1 = GCNConv(2, 16); self.k2 = GCNConv(16, 8)
    def encode(self, x, ei):
        return self.k2(F.relu(self.k1(x, ei)), ei)
    def decode(self, z, ei):
        return (z[ei[0]] * z[ei[1]]).sum(dim=-1)

model = OneriGCN()
optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

for epoch in range(200):
    model.train(); optimizer.zero_grad()
    z = model.encode(veri.x, veri.edge_index)
    neg = negative_sampling(veri.edge_index, veri.num_nodes, veri.edge_index.size(1)//2)
    pos_s = model.decode(z, veri.edge_index)
    neg_s = model.decode(z, neg)
    skor = torch.cat([pos_s, neg_s])
    et = torch.cat([torch.ones(pos_s.size(0)), torch.zeros(neg_s.size(0))])
    loss = F.binary_cross_entropy_with_logits(skor, et)
    loss.backward(); optimizer.step()

# --- Her kullanici icin, SATIN ALMADIGI urunleri puanla, en yuksek 3'u oner ---
print("=== Kişiye özel öneriler ===")
model.eval()
with torch.no_grad():
    z = model.encode(veri.x, veri.edge_index)
    for kullanici in kullanicilar:
        alinanlar = {b for a, b in satin_almalar if a == kullanici}
        skorlar = []
        for urun in urunler:
            if urun not in alinanlar:
                s = torch.sigmoid(model.decode(z, torch.tensor([[idx[kullanici]], [idx[urun]]])))
                skorlar.append((urun, s.item()))
        skorlar.sort(key=lambda x: -x[1])
        print(f"\n{kullanici} için öneriler (satın aldıkları: {', '.join(alinanlar)}):")
        for urun, skor in skorlar[:3]:
            print(f"   {urun:15s} -> olasılık={skor:.3f}")