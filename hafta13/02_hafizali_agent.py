import os
from dotenv import load_dotenv
from anthropic import Anthropic

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

# --- Sınıf (class) kullanarak hafızayı bir "nesne" içinde saklıyoruz ---
class HafizaliAgent:
    def __init__(self):
        # Bu liste, TÜM konuşma boyunca kalıcı olacak - her yeni soru buraya eklenir
        self.mesajlar = []

    def soru_sor(self, kullanici_mesaji: str):
        # Yeni soruyu, önceki tüm geçmişin ÜZERİNE ekliyoruz (silmiyoruz)
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
                    print(f"[Arka planda: {block.name}({block.input}) -> {sonuc}]")

                    self.mesajlar.append({
                        "role": "user",
                        "content": [{
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": sonuc
                        }]
                    })

            son_yanit = client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=1024,
                tools=tools,
                messages=self.mesajlar
            )
            # Nihai cevabı da hafızaya ekliyoruz (bir sonraki soru için bağlam olsun diye)
            self.mesajlar.append({"role": "assistant", "content": son_yanit.content})
            return son_yanit.content[0].text
        else:
            self.mesajlar.append({"role": "assistant", "content": yanit.content})
            return yanit.content[0].text


# --- Çoklu-turlu konuşma testi ---
agent = HafizaliAgent()

print("=" * 60)
print("TUR 1")
print("=" * 60)
cevap1 = agent.soru_sor("101 numaralı numunenin test sonucu nedir?")
print(f"Claude: {cevap1}\n")

print("=" * 60)
print("TUR 2 (önceki bağlama referans veriyoruz, numune ID'sini TEKRAR SÖYLEMİYORUZ)")
print("=" * 60)
cevap2 = agent.soru_sor("Bu mutasyon klinik olarak ne kadar önemli?")
print(f"Claude: {cevap2}\n")

print("=" * 60)
print("TUR 3 (hafızada kaç mesaj birikti, kontrol edelim)")
print("=" * 60)
print(f"Toplam mesaj sayısı hafızada: {len(agent.mesajlar)}")