import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# --- Sahte bir takvim veritabanı (gerçek projede Google Calendar API olurdu) ---
takvim = [
    {"id": 1, "baslik": "TP53 Konsey Toplantısı", "tarih": "2026-09-16", "saat": "10:00"},
    {"id": 2, "baslik": "Roche Mülakat Ön Görüşmesi", "tarih": "2026-09-17", "saat": "14:00"},
]

# --- ARAÇ 1: Takvimdeki etkinlikleri listele ---
def etkinlikleri_listele(tarih: str = None) -> str:
    sonuclar = [e for e in takvim if tarih is None or e["tarih"] == tarih]
    if not sonuclar:
        return "Bu tarihte hiç etkinlik yok."
    return json.dumps(sonuclar, ensure_ascii=False)

# --- ARAÇ 2: Yeni etkinlik ekle ---
def etkinlik_ekle(baslik: str, tarih: str, saat: str) -> str:
    yeni_id = max([e["id"] for e in takvim], default=0) + 1
    yeni_etkinlik = {"id": yeni_id, "baslik": baslik, "tarih": tarih, "saat": saat}
    takvim.append(yeni_etkinlik)
    return f"Etkinlik eklendi: {baslik} - {tarih} {saat} (ID: {yeni_id})"

# --- ARAÇ 3: Çakışma kontrolü ---
def cakisma_kontrol(tarih: str, saat: str) -> str:
    for e in takvim:
        if e["tarih"] == tarih and e["saat"] == saat:
            return f"ÇAKIŞMA VAR: '{e['baslik']}' zaten bu saatte planlanmış."
    return "Çakışma yok, bu saat müsait."

tools = [
    {
        "name": "etkinlikleri_listele",
        "description": "Takvimdeki etkinlikleri listeler. Belirli bir tarih verilirse sadece o güne ait etkinlikleri gösterir.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tarih": {"type": "string", "description": "YYYY-MM-DD formatında tarih (opsiyonel)"}
            }
        }
    },
    {
        "name": "etkinlik_ekle",
        "description": "Takvime yeni bir etkinlik/toplantı ekler.",
        "input_schema": {
            "type": "object",
            "properties": {
                "baslik": {"type": "string", "description": "Etkinliğin başlığı"},
                "tarih": {"type": "string", "description": "YYYY-MM-DD formatında tarih"},
                "saat": {"type": "string", "description": "HH:MM formatında saat"}
            },
            "required": ["baslik", "tarih", "saat"]
        }
    },
    {
        "name": "cakisma_kontrol",
        "description": "Belirli bir tarih ve saatte, takvimde zaten bir etkinlik olup olmadığını kontrol eder.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tarih": {"type": "string", "description": "YYYY-MM-DD formatında tarih"},
                "saat": {"type": "string", "description": "HH:MM formatında saat"}
            },
            "required": ["tarih", "saat"]
        }
    }
]

# --- Araç adı -> gerçek Python fonksiyonu eşlemesi ---
arac_fonksiyonlari = {
    "etkinlikleri_listele": etkinlikleri_listele,
    "etkinlik_ekle": etkinlik_ekle,
    "cakisma_kontrol": cakisma_kontrol,
}

class TakvimAgent:
    def __init__(self):
        self.mesajlar = []

    def soru_sor(self, kullanici_mesaji: str) -> str:
        self.mesajlar.append({"role": "user", "content": kullanici_mesaji})

        # --- Agent, birden fazla adımda birden fazla araç çağırabilir (loop ile) ---
        while True:
            yanit = client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=1024,
                tools=tools,
                messages=self.mesajlar
            )

            if yanit.stop_reason != "tool_use":
                self.mesajlar.append({"role": "assistant", "content": yanit.content})
                return yanit.content[0].text

            # --- Tool use varsa, çağrılan HER aracı işleyip sonuçları topluyoruz ---
            self.mesajlar.append({"role": "assistant", "content": yanit.content})
            tool_sonuclari = []

            for block in yanit.content:
                if block.type == "tool_use":
                    fonksiyon = arac_fonksiyonlari.get(block.name)
                    if fonksiyon:
                        sonuc = fonksiyon(**block.input)
                        print(f"[Arka planda: {block.name}({block.input}) -> {sonuc}]")
                    else:
                        sonuc = f"HATA: Bilinmeyen araç '{block.name}'"

                    tool_sonuclari.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(sonuc)
                    })

            self.mesajlar.append({"role": "user", "content": tool_sonuclari})
            # --- while döngüsü devam ediyor: Claude, ilk tool sonucuna bakıp
            #     ikinci bir araç daha çağırmak isteyebilir (örn. önce çakışma kontrolü,
            #     sonra ekleme) - bu yüzden tek seferlik değil, döngü yapıyoruz ---


agent = TakvimAgent()

print("=" * 60)
print("TEST 1: Basit listeleme")
print("=" * 60)
print(f"Claude: {agent.soru_sor('16 Eylül 2026 tarihinde ne var takvimde?')}\n")

print("=" * 60)
print("TEST 2: Çok-adımlı görev (önce çakışma kontrolü, SONRA ekleme)")
print("=" * 60)
mesaj_2 = "17 Eylül 2026, saat 14:00'e Sanger Doğrulama toplantısı ekle, ama önce o saatte başka bir şey var mı kontrol et"
print(f"Claude: {agent.soru_sor(mesaj_2)}\n")

print("=" * 60)
print("TEST 3: Güncel durumu göster")
print("=" * 60)
mesaj_3 = "Şimdi 17 Eylül'deki tüm etkinlikleri listele"
print(f"Claude: {agent.soru_sor(mesaj_3)}\n")