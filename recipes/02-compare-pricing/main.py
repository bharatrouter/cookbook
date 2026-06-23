"""Prove you're cheaper — live INR price comparison.

The gateway exposes a public endpoint that returns FX-converted INR pricing for a model,
so you can show the saving instead of claiming it.

Run: BHARATROUTER_MODEL=<id> python recipes/02-compare-pricing/main.py
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE = os.getenv("BHARATROUTER_BASE_URL", "https://api.bharatrouter.com/v1")
KEY = os.environ["BHARATROUTER_API_KEY"]
HEADERS = {"Authorization": f"Bearer {KEY}"}


def pick_model() -> str:
    m = os.getenv("BHARATROUTER_MODEL")
    if m:
        return m
    r = requests.get(f"{BASE}/models", headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()["data"][0]["id"]


def compare(model: str) -> dict:
    r = requests.get(f"{BASE}/pricing/compare", params={"model": model}, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


if __name__ == "__main__":
    model = pick_model()
    print(f"Pricing for {model} (INR per 1M tokens):")
    print(compare(model))
