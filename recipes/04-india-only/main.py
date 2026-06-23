"""Guarantee no prompt leaves India.

Pin `data_policy: "india_only"` and the gateway only considers India-resident routes — and
**fails closed** (error) rather than silently routing offshore if none are eligible. We read
the `x-br-provider` response header to confirm who served the request.

Run: python recipes/04-india-only/main.py
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


# with_raw_response gives us the HTTP headers alongside the parsed body.
raw = client.chat.completions.with_raw_response.create(
    model=pick_model(),
    messages=[{"role": "user", "content": "Kripya ek line mein namaste kahein."}],
    extra_body={"data_policy": "india_only"},
)

completion = raw.parse()
print("served by provider:", raw.headers.get("x-br-provider"))
print(completion.choices[0].message.content)

# If you request a model with no India-resident route under india_only, the gateway
# returns an error (no_route) — it never falls back offshore.
