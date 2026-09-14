import os
from dotenv import load_dotenv
from anthropic import Anthropic
from fastapi import FastAPI
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
            "properties": {
                "numune_id": {"type": "string", "description": "Sorgulanacak numunenin ID'si"}
            },
            "required": ["numune_id"]
        }
    }
]

class HafizaliAgent:
    def __init__(self):
        self.mesajlar = []

    def soru_sor(self, kullanici_mesaji: str):
        self.mesajlar.append({"role": "user", "content": kullanici_mesaji})

        yanit = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            tools=tools,
            messages=self.mesajlar
        )

        if yanit.stop_reason == "tool_use":
            self.mesajlar.append({"role": "assistant", "content": yanit.content})

            for block in yanit.content:
                if block.type == "tool_use" and block.name == "numune_sonucu_sorgula":
                    sonuc = numune_sonucu_sorgula(block.input["numune_id"])
                    self.mesajlar.append({
                        "role": "user",
                        "content": [{"type": "tool_result", "tool_use_id": block.id, "content": sonuc}]
                    })

            son_yanit = client.messages.create(
                model="claude-sonnet-4-5", max_tokens=1024, tools=tools, messages=self.mesajlar
            )
            self.mesajlar.append({"role": "assistant", "content": son_yanit.content})
            return son_yanit.content[0].text
        else:
            self.mesajlar.append({"role": "assistant", "content": yanit.content})
            return yanit.content[0].text


# --- FastAPI uygulamasını başlatıyoruz ---
app = FastAPI(title="Klinik Agent API")

# --- Her kullanıcı için AYRI bir agent (hafıza) tutmak için basit bir sözlük ---
oturumlar = {}

# --- Gelen isteğin (request) hangi alanları içermesi gerektiğini tanımlıyoruz ---
class SoruIstegi(BaseModel):
    oturum_id: str
    soru: str

@app.post("/soru-sor")
def soru_sor_endpoint(istek: SoruIstegi):
    # Eğer bu oturum_id ile daha önce hiç agent oluşturmadıysak, yeni bir tane oluştur
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
    return {"durum": "Agent API çalışıyor", "endpoint": "/soru-sor (POST)"}