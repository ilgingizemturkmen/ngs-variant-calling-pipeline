import boto3
from botocore.exceptions import NoCredentialsError, ClientError
import torch
import torch.nn as nn

# --- Aynı model mimarisi (Hafta 14 Adım 2-3'ten) ---
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


def modeli_s3ye_yukle(yerel_dosya: str, bucket_adi: str, s3_anahtar: str):
    """
    Eğitilmiş modeli AWS S3'e yükler.
    Gerçek AWS hesabı olduğunda, 'aws configure' ile kimlik bilgilerini
    girdikten sonra bu fonksiyon HİÇBİR DEĞİŞİKLİK olmadan çalışır.
    """
    s3 = boto3.client("s3")
    try:
        s3.upload_file(yerel_dosya, bucket_adi, s3_anahtar)
        print(f"BAŞARILI: '{yerel_dosya}' -> s3://{bucket_adi}/{s3_anahtar}")
    except NoCredentialsError:
        print("SİMÜLASYON: AWS kimlik bilgisi bulunamadı (beklenen davranış).")
        print(f"Gerçek hesapta bu satır çalışsaydı, model şuraya yüklenirdi:")
        print(f"  s3://{bucket_adi}/{s3_anahtar}")
    except ClientError as e:
        print(f"AWS hata verdi: {e}")


def modeli_s3ten_indir(bucket_adi: str, s3_anahtar: str, hedef_dosya: str):
    """Bir EC2 instance'ının, S3'teki modeli indirip kullanmasını simüle eder."""
    s3 = boto3.client("s3")
    try:
        s3.download_file(bucket_adi, s3_anahtar, hedef_dosya)
        print(f"BAŞARILI: s3://{bucket_adi}/{s3_anahtar} -> '{hedef_dosya}'")
    except NoCredentialsError:
        print("SİMÜLASYON: Gerçek hesapta, EC2 instance'ı bu modeli S3'ten")
        print(f"  indirip yerel diskine (' {hedef_dosya}') kaydederdi.")
    except ClientError as e:
        print(f"AWS hata verdi: {e}")


# --- 1. Modeli eğitip (ya da kaydedilmiş olanı yükleyip) S3'e "yüklemeyi" deneyelim ---
print("=" * 60)
print("SENARYO: Eğitilmiş modeli production'a taşıma")
print("=" * 60)

model = PatojeniteSiniflandirici()
model.load_state_dict(torch.load("patojenite_modeli.pt"))
print("Model diskten yüklendi (yerel dosya: patojenite_modeli.pt)\n")

BUCKET_ADI = "gizem-genomik-modeller"  # gerçek hesapta bu, senin oluşturduğun bir S3 bucket adı olurdu
S3_ANAHTAR = "modeller/patojenite_v1.pt"

print("--- Adım A: Modeli S3'e yükle ---")
modeli_s3ye_yukle("patojenite_modeli.pt", BUCKET_ADI, S3_ANAHTAR)

print("\n--- Adım B: (Farklı bir EC2 instance'ında) modeli S3'ten indir ---")
modeli_s3ten_indir(BUCKET_ADI, S3_ANAHTAR, "indirilen_model.pt")

print("\n" + "=" * 60)
print("NEDEN BU MİMARİ KULLANILIR?")
print("=" * 60)
print("""
1. Model eğitimi (GPU-yoğun) -> güçlü bir EC2 instance'ında (örn. g4dn.xlarge) yapılır
2. Eğitim biter, model S3'e yüklenir (kalıcı, ucuz depolama)
3. Production API'si (Hafta 13'teki FastAPI gibi) -> küçük, ucuz bir EC2/Lambda'da çalışır
4. API başlarken S3'ten modeli indirir, belleğe yükler, istekleri cevaplar
5. Model güncellenmek istendiğinde -> sadece S3'teki dosya değiştirilir,
   API'nin kodu değişmez, yeniden başlatıldığında yeni modeli otomatik çeker

Bu ayrım (eğitim ortamı vs sunum/inference ortamı) production ML mimarisinin
temel prensiplerinden biridir - eğitim için kullanılan pahalı GPU makinesini
7/24 açık tutmaya gerek yoktur, sadece eğitim sırasında kullanılır.
""")