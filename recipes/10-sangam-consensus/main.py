"""Higher-quality answers with Sangam consensus.

Sangam is BharatRouter's consensus feature: a panel of models answers in parallel and a
synthesizer reconciles one best answer. Call it like any model id, or define a custom panel.

Run: python recipes/10-sangam-consensus/main.py
"""
import os
import requests
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

BASE = os.getenv("BHARATROUTER_BASE_URL", "https://api.bharatrouter.com/v1")
KEY = os.environ["BHARATROUTER_API_KEY"]
client = OpenAI(base_url=BASE, api_key=KEY)

PROMPT = "What are two trade-offs of prepaid vs postpaid API billing? Be concise."

# 1) Built-in consensus — just use the model id.
resp = client.chat.completions.create(
    model="bharatrouter/sangam",
    messages=[{"role": "user", "content": PROMPT}],
)
print("=== bharatrouter/sangam ===")
print(resp.choices[0].message.content)


# 2) Custom panel — pick any 2-6 model ids from your catalog; a synthesizer reconciles them.
def catalog_ids(n: int) -> list[str]:
    r = requests.get(f"{BASE}/models", headers={"Authorization": f"Bearer {KEY}"}, timeout=30)
    r.raise_for_status()
    return [m["id"] for m in r.json()["data"][:n]]


panel = catalog_ids(3)
custom = client.chat.completions.create(
    model="bharatrouter/sangam",
    messages=[{"role": "user", "content": PROMPT}],
    extra_body={"sangam": {"panel": panel, "synth": panel[0]}},
)
print(f"\n=== custom panel {panel} ===")
print(custom.choices[0].message.content)
