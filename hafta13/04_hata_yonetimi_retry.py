import os
import time
from dotenv import load_dotenv
from anthropic import Anthropic, APIError, APIConnectionError, RateLimitError
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def numune_sonucu_sorgula(numune_id: str) -> str:
    sahte_veritabani = {
        "101": "TP53_Sekans: MUT_R175H, AF=0.977",
        "102": "BRCA1_Sekans: WT",
        "103": "BCR-ABL1_Fusion: POZITIF",
    }
    return sahte_veritabani.get(numune_id, "Numune bulunamadı")

tools = [
    {
        "name": "numune_sonucu_sorgula",
        "description": "Belirli bir numune ID'sinin laboratuvar test sonucunu getirir.",
        "input_schema": {
            "type": "object",
            "properties": {"numune_id": {"type": "string", "description": "Sorgulanacak numunenin ID'si"}},
            "required": ["numune_id"]
        }
    }
]

# --- Retry mantığını içeren, güvenli bir API çağrı fonksiyonu ---
def guvenli_api_cagrisi(mesajlar, maks_deneme=3):
    """
    Anthropic API'ye istek atar. Geçici hatalarda (bağlantı/rate limit)
    otomatik olarak yeniden dener - üstel bekleme (exponential backoff) ile.
    """
    for deneme in range(1, maks_deneme + 1):
        try:
            return client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=1024,
                tools=tools,
                messages=mesajlar
            )
        except RateLimitError as e:
            # Rate limit'e takıldık - biraz bekleyip tekrar deneriz
            bekleme_suresi = 2 ** deneme  # 1. denemede 2sn, 2.de 4sn, 3.te 8sn (exponential backoff)
            print(f"[UYARI] Rate limit aşıldı (deneme {deneme}/{maks_deneme}). {bekleme_suresi}sn bekleniyor...")
            if deneme == maks_deneme:
                raise  # son denemede de olmazsa, hatayı yukarı fırlat
            time.sleep(bekleme_suresi)
        except APIConnectionError as e:
            # Ağ bağlantı sorunu - muhtemelen geçici, tekrar deneriz
            print(f"[UYARI] Bağlantı hatası (deneme {deneme}/{maks_deneme}): {e}")
            if deneme == maks_deneme:
                raise
            time.sleep(2)
        except APIError as e:
            # Diğer API hataları (örn. geçersiz istek) - tekrar denemenin faydası yok
            print(f"[HATA] API hatası, tekrar denenmeyecek: {e}")
            raise


class HafizaliAgent:
    def __init__(self):
        self.mesajlar = []

    def soru_sor(self, kullanici_mesaji: str) -> str:
        self.mesajlar.append({"role": "user", "content": kullanici_mesaji})

        try:
            yanit = guvenli_api_cagrisi(self.mesajlar)
        except Exception as e:
            # Tüm denemeler başarısız oldu - kullanıcıya anlamlı bir mesaj döndür
            # (ham hatayı göstermek yerine, ne olduğunu Türkçe açıklıyoruz)
            self.mesajlar.pop()  # başarısız isteği hafızadan çıkar, kirli kalmasın
            return f"Üzgünüm, şu anda sisteme ulaşamıyorum. Lütfen birkaç dakika sonra tekrar deneyin. (Teknik detay: {type(e).__name__})"

        if yanit.stop_reason == "tool_use":
            self.mesajlar.append({"role": "assistant", "content": yanit.content})

            for block in yanit.content:
                if block.type == "tool_use" and block.name == "numune_sonucu_sorgula":
                    try:
                        sonuc = numune_sonucu_sorgula(block.input["numune_id"])
                    except Exception as e:
                        sonuc = f"HATA: Numune sorgusu başarısız oldu ({e})"

                    self.mesajlar.append({
                        "role": "user",
                        "content": [{"type": "tool_result", "tool_use_id": block.id, "content": sonuc}]
                    })

            try:
                son_yanit = guvenli_api_cagrisi(self.mesajlar)
            except Exception as e:
                return f"Üzgünüm, sonucu yorumlarken bir sorun oluştu. Lütfen tekrar deneyin. (Teknik detay: {type(e).__name__})"

            self.mesajlar.append({"role": "assistant", "content": son_yanit.content})
            return son_yanit.content[0].text
        else:
            self.mesajlar.append({"role": "assistant", "content": yanit.content})
            return yanit.content[0].text


app = FastAPI(title="Klinik Agent API (Hata Yönetimli)")
oturumlar = {}

class SoruIstegi(BaseModel):
    oturum_id: str
    soru: str

@app.post("/soru-sor")
def soru_sor_endpoint(istek: SoruIstegi):
    # --- Girdi doğrulama: boş soru gelirse anlamlı bir hata döndür ---
    if not istek.soru.strip():
        raise HTTPException(status_code=400, detail="Soru alanı boş olamaz.")

    if istek.oturum_id not in oturumlar:
        oturumlar[istek.oturum_id] = HafizaliAgent()

    agent = oturumlar[istek.oturum_id]
    cevap = agent.soru_sor(istek.soru)

    return {
        "oturum_id": istek.oturum_id,
        "cevap": cevap,
        "hafizadaki_mesaj_sayisi": len(agent.mesajlar)
    }

@app.get("/")
def ana_sayfa():
    return {"durum": "Agent API çalışıyor (hata yönetimli)", "endpoint": "/soru-sor (POST)"}