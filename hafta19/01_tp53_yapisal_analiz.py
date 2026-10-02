from Bio.PDB import PDBList, PDBParser
import warnings
warnings.filterwarnings("ignore")  # PDB parser'ın bazı rutin uyarılarını gizle

# --- 1TUP: TP53 DNA-bağlanma domaini + DNA + Zn iyonu - gerçek, deneysel kristal yapı ---
# (Cho et al. 1994, Science - p53 tumor suppressor'ın ilk yapısal çözümü)
pdb_id = "1TUP"

print(f"=== {pdb_id} kristal yapısı PDB'den indiriliyor ===")
pdbl = PDBList()
dosya_yolu = pdbl.retrieve_pdb_file(pdb_id, pdir=".", file_format="pdb")

parser = PDBParser(QUIET=True)
yapi = parser.get_structure(pdb_id, dosya_yolu)

print(f"Yapı başarıyla yüklendi: {pdb_id}")
print(f"Model sayısı: {len(yapi)}")

model = yapi[0]
print(f"Zincir (chain) sayısı: {len(model)}")
for zincir in model:
    kalinti_sayisi = len(list(zincir.get_residues()))
    print(f"  Zincir {zincir.id}: {kalinti_sayisi} kalıntı/atom grubu")

# --- R175'i bul (A zinciri, protein zinciri olmalı) ---
print("\n=== Kalıntı 175'i arıyoruz ===")
protein_zinciri = model["A"]  # 1TUP'ta "auth A" = p53 DNA-bağlanma domaini (RCSB'de doğrulandı)

try:
    kalinti_175 = protein_zinciri[175]
    print(f"Bulundu: {kalinti_175.get_resname()} 175")
    print("(Beklenen: ARG - Arginin, çünkü mutasyon öncesi yabani tip bu pozisyonda Arginin taşır)")
except KeyError:
    print("Kalıntı 175 bu zincirde doğrudan bulunamadı, numaralandırma farklı olabilir.")

# --- Çinko (Zn) iyonunu SADECE A zincirinde ara (R175 ile aynı protomer) ---
print("\n=== Çinko (Zn) iyonunu A zincirinde arıyoruz ===")
zn_atomu = None
for kalinti in protein_zinciri:
    if kalinti.get_resname() == "ZN":
        zn_atomu = kalinti["ZN"]
        print(f"Zn iyonu bulundu: A zinciri içinde, kalıntı {kalinti.id}")

if zn_atomu is None:
    print("A zincirinde Zn iyonu bulunamadı.")
else:
    # --- R175'in CA (alfa karbon) atomu ile Zn arasındaki mesafeyi hesapla ---
    ca_175 = kalinti_175["CA"]
    mesafe = ca_175 - zn_atomu
    print(f"\nR175 (CA atomu) ile Zn iyonu arasındaki mesafe: {mesafe:.2f} Angstrom")
    print("(Yorum: <10 Angstrom ise, R175 çinko-bağlanma bölgesine YAKIN -> YAPISAL rol)")