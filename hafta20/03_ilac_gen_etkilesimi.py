import torch
import torch.nn.functional as F
from torch_geometric.data import Data
from torch_geometric.nn import GCNConv
from torch_geometric.utils import negative_sampling

torch.manual_seed(42)

# --- Node'lar: 5 ilaç + 5 gen, tek bir graf içinde ---
isimler = ["Ilac_A", "Ilac_B", "Ilac_C", "Ilac_D", "Ilac_E",
           "GenX", "GenY", "GenZ", "GenW", "GenV"]
idx = {isim: i for i, isim in enumerate(isimler)}

# Ozellik: [tip (0=ilac, 1=gen), aktivite_skoru (rastgele, ogrenim amacli)]
ozellikler = torch.tensor([
    [0, 0.8], [0, 0.6], [0, 0.4], [0, 0.9], [0, 0.3],   # ilaclar
    [1, 0.7], [1, 0.5], [1, 0.6], [1, 0.2], [1, 0.8],   # genler
], dtype=torch.float)

# --- Bilinen etkilesimler (egitim verisi) ---
bilinen_etkilesimler = [
    ("Ilac_A", "GenX"), ("Ilac_A", "GenY"), ("Ilac_B", "GenY"),
    ("Ilac_C", "GenZ"), ("Ilac_D", "GenX"), ("Ilac_D", "GenW"),
]
kaynak, hedef = [], []
for a, b in bilinen_etkilesimler:
    kaynak += [idx[a], idx[b]]
    hedef += [idx[b], idx[a]]
edge_index = torch.tensor([kaynak, hedef], dtype=torch.long)

veri = Data(x=ozellikler, edge_index=edge_index)

class LinkGCN(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.katman1 = GCNConv(2, 16)
        self.katman2 = GCNConv(16, 8)

    def encode(self, x, edge_index):
        x = F.relu(self.katman1(x, edge_index))
        return self.katman2(x, edge_index)

    def decode(self, z, edge_label_index):
        # iki node'un embedding'inin ic carpimi -> "bu ikisi baglantili mi" skoru
        return (z[edge_label_index[0]] * z[edge_label_index[1]]).sum(dim=-1)

model = LinkGCN()
optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

print("Eğitim başlıyor (link prediction)...\n")
for epoch in range(1, 201):
    model.train()
    optimizer.zero_grad()

    z = model.encode(veri.x, veri.edge_index)

    # --- Negatif ornekleme: rastgele, GERCEKTE OLMAYAN ciftler uret ---
    neg_edge_index = negative_sampling(
        edge_index=veri.edge_index, num_nodes=veri.num_nodes,
        num_neg_samples=veri.edge_index.size(1) // 2)

    pos_skor = model.decode(z, veri.edge_index)
    neg_skor = model.decode(z, neg_edge_index)

    skorlar = torch.cat([pos_skor, neg_skor])
    etiketler = torch.cat([torch.ones(pos_skor.size(0)), torch.zeros(neg_skor.size(0))])

    loss = F.binary_cross_entropy_with_logits(skorlar, etiketler)
    loss.backward()
    optimizer.step()

    if epoch % 50 == 0:
        print(f"Epoch {epoch} | Loss: {loss.item():.4f}")

# --- Egitim sonrasi: HIC gormedigimiz tum ilac-gen ciftlerini puanla ---
print("\n=== Tüm ilaç-gen çiftleri için tahmin skoru ===")
model.eval()
with torch.no_grad():
    z = model.encode(veri.x, veri.edge_index)
    for ilac in isimler[:5]:
        for gen in isimler[5:]:
            skor = torch.sigmoid(model.decode(z, torch.tensor([[idx[ilac]], [idx[gen]]])))
            bilinen = (ilac, gen) in bilinen_etkilesimler
            etiket = "[BİLİNEN]" if bilinen else ""
            print(f"{ilac:8s} - {gen:6s} | olasılık={skor.item():.3f} {etiket}")