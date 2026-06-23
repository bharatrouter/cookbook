"""Never return an error — failover chain.

Provide an ordered fallback chain on the request: if the first route is down or rate-limited,
the gateway falls through to the next, with circuit-breaker failover. Here we build the chain
from your own catalog so nothing is hard-coded.

Run: python recipes/03-failover-chain/main.py
"""
import os
import requests
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

BASE = os.getenv("BHARATROUTER_BASE_URL", "https://api.bharatrouter.com/v1")
KEY = os.environ["BHARATROUTER_API_KEY"]
client = OpenAI(base_url=BASE, api_key=KEY)


def catalog_ids(n: int = 3) -> list[str]:
    """First few model ids from your live catalog — order is yours to decide."""
    r = requests.get(f"{BASE}/models", headers={"Authorization": f"Bearer {KEY}"}, timeout=30)
    r.raise_for_status()
    return [m["id"] for m in r.json()["data"][:n]]


ids = catalog_ids()
primary, *rest = ids

resp = client.chat.completions.create(
    model=primary,
    messages=[{"role": "user", "content": "Give me a one-line status update template."}],
    # Tried in order; the gateway skips dead/rate-limited routes automatically.
    extra_body={"fallbacks": [{"model": m} for m in rest]},
)

print("chain:", " -> ".join(ids))
print("served by:", resp.model)
print(resp.choices[0].message.content)
