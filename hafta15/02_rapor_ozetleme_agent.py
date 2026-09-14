import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# --- Ham, teknik bir laboratuvar raporu (gerçek bir NGS rapor formatına benzer) ---
HAM_RAPOR = """
NUMUNE ID: 101
TEST: TP53 Gen Sekans Analizi (NGS Panel)
BULGU: c.524G>A (p.Arg175His), Heterozigot
ALEL FREKANSI: 0.977
KAPLAMA DERİNLİĞİ: 847x
CLINVAR SINIFLANDIRMASI: Patojenik
COSMIC ID: COSM10662
İLİŞKİLİ SENDROM: Li-Fraumeni Sendromu (LFS)
KALITIM PATERNİ: Otozomal Dominant
NOT: Bu varyant, TP53'ün DNA bağlanma domainini etkileyen bilinen bir
hotspot mutasyonudur. Germline kökenli olması durumunda, hastanın
birinci derece akrabalarına genetik danışmanlık önerilir.
"""

# --- Farklı hedef kitleler için farklı "persona" tanımları (system prompt) ---
PERSONALAR = {
    "hasta": """Sen, hastalara tıbbi sonuçları açıklayan empatik bir genetik danışmansın.
Tıbbi jargon kullanma, basit ve anlaşılır bir dille yaz. Kaygı yaratmadan,
ama dürüst ve net bilgi ver. Teknik terimleri (varyant, alel frekansı gibi)
günlük dile çevir. 3-4 kısa paragraf yeterli.""",

    "hekim": """Sen, bir onkoloğa/genetik uzmanına teknik bir varyant raporu
özetleyen bir klinik biyoinformatikçisin. Tıbbi terminolojiyi koru, kısa ve
öz ol, klinik karar açısından en önemli noktaları öne çıkar (patojenite,
kalıtım paterni, önerilen aksiyon). Madde işaretleri kullanabilirsin.""",

    "sigorta": """Sen, bir sigorta şirketine sunulacak resmi bir tıbbi özet
hazırlayan bir raportörsün. Tarafsız, objektif, sadece doğrulanmış bulguları
içeren, yorum katmayan resmi bir dil kullan. Teşhis kodları ve tıbbi
terminoloji uygun, ama gereksiz klinik detaya girme."""
}


def rapor_ozetle(ham_rapor: str, hedef_kitle: str) -> str:
    """
    Aynı ham raporu, farklı 'persona' (system prompt) kullanarak
    farklı hedef kitleler için yeniden yazar.
    """
    if hedef_kitle not in PERSONALAR:
        raise ValueError(f"Bilinmeyen hedef kitle: {hedef_kitle}")

    yanit = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        system=PERSONALAR[hedef_kitle],  # <-- persona burada, system prompt olarak veriliyor
        messages=[
            {"role": "user", "content": f"Şu laboratuvar raporunu özetle:\n\n{ham_rapor}"}
        ]
    )
    return yanit.content[0].text


# --- Aynı ham veriyi, 3 farklı hedef kitle için özetleyelim ---
for kitle in ["hasta", "hekim", "sigorta"]:
    print("=" * 60)
    print(f"HEDEF KİTLE: {kitle.upper()}")
    print("=" * 60)
    ozet = rapor_ozetle(HAM_RAPOR, kitle)
    print(ozet)
    print()