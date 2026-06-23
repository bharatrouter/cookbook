"""Build a Hindi / Indic chatbot.

Serve Indian-language chat on India-resident routes (pin with `data_policy: "india_only"`).
Pick any Indic-capable model from the catalog via BHARATROUTER_MODEL.

Run: python recipes/06-indic-chatbot/main.py
"""
import os
import requests
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

BASE = os.getenv("BHARATROUTER_BASE_URL", "https://api.bharatrouter.com/v1")
KEY = os.environ["BHARATROUTER_API_KEY"]
client = OpenAI(base_url=BASE, api_key=KEY)


def pick_model() -> str:
    m = os.getenv("BHARATROUTER_MODEL")
    if m:
        return m
    r = requests.get(f"{BASE}/models", headers={"Authorization": f"Bearer {KEY}"}, timeout=30)
    r.raise_for_status()
    return r.json()["data"][0]["id"]


messages = [
    {"role": "system", "content": "Aap ek sahaayak hain. Hindi mein saral javaab dein."},
    {"role": "user", "content": "Bengaluru mein aaj mausam ke hisaab se kya pehnein?"},
]

resp = client.chat.completions.create(
    model=pick_model(),
    messages=messages,
    extra_body={"data_policy": "india_only"},
)
print(resp.choices[0].message.content)
