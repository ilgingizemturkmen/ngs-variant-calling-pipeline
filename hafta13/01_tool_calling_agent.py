import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def numune_sonucu_sorgula(numune_id: str) -> str:
    """Gerçek bir veritabanı sorgusu olsaydı buraya SQL/DuckDB kodu gelirdi."""
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
                "numune_id": {
                    "type": "string",
                    "description": "Sorgulanacak numunenin ID'si, örn. '101'"
                }
            },
            "required": ["numune_id"]
        }
    }
]

def agent_calistir(kullanici_mesaji: str):
    mesajlar = [{"role": "user", "content": kullanici_mesaji}]

    yanit = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        tools=tools,
        messages=mesajlar
    )

    print(f"Claude'un durma nedeni: {yanit.stop_reason}")

    if yanit.stop_reason == "tool_use":
        for block in yanit.content:
            if block.type == "tool_use":
                print(f"Claude şu aracı çağırmak istiyor: {block.name}")
                print(f"Parametreler: {block.input}")

                if block.name == "numune_sonucu_sorgula":
                    sonuc = numune_sonucu_sorgula(block.input["numune_id"])
                    print(f"Fonksiyon sonucu: {sonuc}")

                    mesajlar.append({"role": "assistant", "content": yanit.content})
                    mesajlar.append({
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
                        messages=mesajlar
                    )
                    print(f"\nClaude'un nihai cevabı:\n{son_yanit.content[0].text}")
    else:
        print(f"\nClaude'un cevabı (tool kullanmadı):\n{yanit.content[0].text}")

print("=" * 60)
print("TEST 1: Numune sorgusu gerektiren soru")
print("=" * 60)
agent_calistir("101 numaralı numunenin test sonucu nedir?")

print("\n" + "=" * 60)
print("TEST 2: Tool gerektirmeyen genel bir soru")
print("=" * 60)
agent_calistir("TP53 geni ne işe yarar, kısaca anlat")