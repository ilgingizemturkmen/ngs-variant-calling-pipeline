# Gerçek GCP kullanmak için: pip install google-cloud-storage
# Kurulu değilse veya kimlik bilgisi yoksa, script çökmeden simülasyon moduna geçer.

BUCKET_ADI = "gizem-genomik-modeller"
YEREL_DOSYA = "lora_adaptor/adapter_model.safetensors"
NESNE_ADI = "modeller/rapor_lora_v1.safetensors"

# =========================================================
# BÖLÜM 1: AWS ↔ GCP karşılığı (isimler farklı, kavramlar aynı)
# =========================================================
esleme = [
    ("Nesne depolama (dosya deposu)", "AWS S3",              "Google Cloud Storage"),
    ("Sanal sunucu",                  "AWS EC2",             "Compute Engine"),
    ("ML/AI platformu",               "AWS SageMaker/Bedrock", "Gemini Enterprise Agent Platform (eski adı Vertex AI)"),
    ("Kimlik/yetki yönetimi",         "AWS IAM",             "Cloud IAM"),
    ("Veri ambarı (SQL analitik)",    "AWS Redshift/Athena", "BigQuery"),
]
print("=" * 78)
print(f"{'Kavram':32s} | {'AWS':22s} | GCP")
print("=" * 78)
for kavram, aws, gcp in esleme:
    print(f"{kavram:32s} | {aws:22s} | {gcp}")

# =========================================================
# BÖLÜM 2: Kod karşılaştırması - aynı iş, iki SDK
# =========================================================
print("\n" + "=" * 78)
print("AYNI İŞ (modeli buluta yükle), İKİ SDK")
print("=" * 78)
print(f"""
AWS (Hafta 14):
    s3 = boto3.client("s3")
    s3.upload_file("{YEREL_DOSYA}", "{BUCKET_ADI}", "{NESNE_ADI}")

GCP (bugün):
    istemci = storage.Client()
    kova = istemci.bucket("{BUCKET_ADI}")
    kova.blob("{NESNE_ADI}").upload_from_filename("{YEREL_DOSYA}")
""")

# =========================================================
# BÖLÜM 3: Gerçek GCP çağrısını dene, kimlik yoksa simülasyona geç
# =========================================================
try:
    from google.cloud import storage
    from google.auth.exceptions import DefaultCredentialsError
except ImportError:
    storage = None

if storage is None:
    print("SİMÜLASYON: google-cloud-storage kurulu değil.")
    print(f"Gerçek hesapta dosya şuraya yüklenirdi: gs://{BUCKET_ADI}/{NESNE_ADI}")
else:
    try:
        istemci = storage.Client()
        kova = istemci.bucket(BUCKET_ADI)
        kova.blob(NESNE_ADI).upload_from_filename(YEREL_DOSYA)
        print(f"BAŞARILI: {YEREL_DOSYA} -> gs://{BUCKET_ADI}/{NESNE_ADI}")
    except DefaultCredentialsError:
        print("SİMÜLASYON: GCP kimlik bilgisi bulunamadı (beklenen davranış).")
        print(f"Gerçek hesapta dosya şuraya yüklenirdi: gs://{BUCKET_ADI}/{NESNE_ADI}")
    except Exception as hata:
        print(f"GCP hata verdi: {type(hata).__name__}")

print("""
FARKLAR (isim dışında):
- Adres biçimi: AWS 's3://kova/anahtar', GCP 'gs://kova/nesne'
- Kimlik: AWS 'aws configure' (anahtar çifti), GCP 'gcloud auth application-default login'
- Kavramsal olarak aynı: önce kova (bucket), içinde nesne (object)
""")