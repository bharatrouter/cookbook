"""Cut your inference bill.

Default to the cheapest eligible route with `optimize: "price"`, and delegate routine work
to whatever model you've chosen — reserving heavier calls for when they earn it.

Run: python recipes/01-cut-inference-costs/main.py
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
    """Use BHARATROUTER_MODEL if set, else let the live catalog decide — no hard-coded vendor."""
    m = os.getenv("BHARATROUTER_MODEL")
    if m:
        return m
    r = requests.get(f"{BASE}/models", headers={"Authorization": f"Bearer {KEY}"}, timeout=30)
    r.raise_for_status()
    return r.json()["data"][0]["id"]


def cheapest(prompt: str, model: str) -> str:
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        extra_body={"optimize": "price"},  # the default — explicit here to show intent
    )
    return f"[{resp.model}] {resp.choices[0].message.content}"


if __name__ == "__main__":
    model = pick_model()
    print(cheapest("Extract the city from: 'Ship it to MG Road, Bengaluru 560001'.", model))
    print(cheapest("Summarise the case for prepaid INR billing in one sentence.", model))
