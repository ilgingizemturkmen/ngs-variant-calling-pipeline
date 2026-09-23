import json
from datetime import datetime

# =========================================================
# BÖLÜM 1: FAIR PRENSİPLERİ (kavramsal + pratik kontrol listesi)
# =========================================================

print("=" * 60)
print("FAIR VERİ PRENSİPLERİ")
print("=" * 60)
print("""
F - Findable (Bulunabilir):     Verinin benzersiz, kalıcı bir kimliği
                                  (ID) olmalı, aranabilir metadata içermeli
A - Accessible (Erişilebilir):  Veri, standart bir protokolle (API, vs.)
                                  erişilebilir olmalı (gerekirse yetkilendirmeyle)
I - Interoperable (Birlikte     Veri, ortak bir dil/format kullanmalı
    Çalışabilir):                 (HL7 FHIR gibi) - farklı sistemler
                                  birbirini anlayabilmeli
R - Reusable (Yeniden           Verinin lisansı, kaynağı, üretim yöntemi
    Kullanılabilir):              açıkça belgelenmiş olmalı
""")

# --- Senin TP53 bulgunu, FAIR kontrol listesiyle değerlendirelim ---
def fair_degerlendirme(varyant_verisi: dict) -> dict:
    sonuc = {}
    sonuc["Findable"] = "id" in varyant_verisi and "kaynak_veritabani_id" in varyant_verisi
    sonuc["Accessible"] = "erisim_yontemi" in varyant_verisi
    sonuc["Interoperable"] = "standart_format" in varyant_verisi
    sonuc["Reusable"] = "lisans" in varyant_verisi and "uretim_yontemi" in varyant_verisi
    return sonuc

# --- Ham (FAIR olmayan) veri - sadece senin bildiğin format ---
ham_varyant = {
    "gen": "TP53",
    "mutasyon": "R175H",
    "af": 0.977
}

# --- FAIR hale getirilmiş versiyon ---
fair_varyant = {
    "id": "urn:uuid:8f14e45f-ceea-4c3d-8e5f-b1a2c3d4e5f6",  # benzersiz, kalıcı kimlik
    "kaynak_veritabani_id": "ClinVar:VCV000012345",          # dış veritabanına bağlantı
    "erisim_yontemi": "FHIR REST API - GET /Observation/{id}",
    "standart_format": "HL7 FHIR R4",
    "lisans": "CC-BY-4.0",
    "uretim_yontemi": "GATK4 HaplotypeCaller v4.5, NGS panel, 847x coverage",
    "gen": "TP53",
    "mutasyon": "c.524G>A (p.Arg175His)",
    "af": 0.977
}

print("--- Ham veri FAIR değerlendirmesi ---")
print(json.dumps(fair_degerlendirme(ham_varyant), indent=2, ensure_ascii=False))

print("\n--- FAIR hale getirilmiş veri değerlendirmesi ---")
print(json.dumps(fair_degerlendirme(fair_varyant), indent=2, ensure_ascii=False))


# =========================================================
# BÖLÜM 2: HL7 FHIR - Varyantı Resmi Standarda Çevirme
# =========================================================

print("\n" + "=" * 60)
print("HL7 FHIR: Genomik Varyantı 'Observation' Kaynağına Çevirme")
print("=" * 60)

def varyant_to_fhir_observation(hasta_id: str, gen: str, hgvs_c: str, hgvs_p: str,
                                  af: float, klinik_anlam: str, rapor_tarihi: str) -> dict:
    """
    Bir genetik varyant bulgusunu, HL7 FHIR R4 'Observation' kaynağı
    formatına çevirir. Bu format, dünya çapında hastane/laboratuvar
    sistemlerinin ortak dilidir - bir sistemde üretilen bu JSON,
    başka bir ülkedeki başka bir sistemde de anlamlı şekilde okunabilir.
    """
    return {
        "resourceType": "Observation",
        "id": f"variant-{gen.lower()}-{hgvs_p.lower().replace('.', '').replace('(', '').replace(')', '')}",
        "status": "final",
        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "laboratory",
                "display": "Laboratory"
            }]
        }],
        "code": {
            "coding": [{
                "system": "http://loinc.org",
                "code": "69548-6",
                "display": "Genetic variant assessment"
            }]
        },
        "subject": {
            "reference": f"Patient/{hasta_id}"
        },
        "effectiveDateTime": rapor_tarihi,
        "component": [
            {
                "code": {"coding": [{"system": "http://loinc.org", "code": "48018-6", "display": "Gene studied"}]},
                "valueCodeableConcept": {"coding": [{"system": "http://www.genenames.org", "display": gen}]}
            },
            {
                "code": {"coding": [{"system": "http://loinc.org", "code": "48004-6", "display": "DNA change (c.HGVS)"}]},
                "valueString": hgvs_c
            },
            {
                "code": {"coding": [{"system": "http://loinc.org", "code": "48005-3", "display": "Amino acid change (p.HGVS)"}]},
                "valueString": hgvs_p
            },
            {
                "code": {"coding": [{"system": "http://loinc.org", "code": "81258-6", "display": "Allelic frequency"}]},
                "valueQuantity": {"value": af, "unit": "fraction"}
            },
            {
                "code": {"coding": [{"system": "http://loinc.org", "code": "53037-8", "display": "Genetic variation clinical significance"}]},
                "valueCodeableConcept": {"coding": [{"system": "http://loinc.org", "display": klinik_anlam}]}
            }
        ]
    }

# --- Senin gerçek TP53 R175H bulgunu FHIR formatına çeviriyoruz ---
fhir_kaydi = varyant_to_fhir_observation(
    hasta_id="patient-101",
    gen="TP53",
    hgvs_c="c.524G>A",
    hgvs_p="p.Arg175His",
    af=0.977,
    klinik_anlam="Pathogenic",
    rapor_tarihi=datetime(2026, 1, 15).isoformat()
)

print(json.dumps(fhir_kaydi, indent=2, ensure_ascii=False))

# --- Diske kaydet (gerçek bir FHIR sunucusuna POST edilebilecek formatta) ---
with open("tp53_variant_fhir.json", "w", encoding="utf-8") as f:
    json.dump(fhir_kaydi, f, indent=2, ensure_ascii=False)

print("\nFHIR kaydı 'tp53_variant_fhir.json' olarak kaydedildi.")
print("Bu dosya, gerçek bir FHIR sunucusuna (örn. HAPI FHIR) doğrudan POST edilebilir formattadır.")