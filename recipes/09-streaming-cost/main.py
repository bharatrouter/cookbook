"""Stream tokens and know the exact ₹ cost.

Stream the response for low latency, ask for usage in the final chunk
(`stream_options.include_usage`), then price it in INR from the live catalog.

Run: python recipes/09-streaming-cost/main.py
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


def inr_rates(model: str) -> tuple[float, float]:
    """(input, output) INR per 1M tokens for the cheapest route of `model`, from /v1/models."""
    r = requests.get(f"{BASE}/models", headers={"Authorization": f"Bearer {KEY}"}, timeout=30)
    r.raise_for_status()
    for m in r.json()["data"]:
        if m["id"] == model:
            routes = m.get("routes") or [{}]
            cheapest = min(routes, key=lambda x: x.get("inputINRPerMtok", 1e9))
            return cheapest.get("inputINRPerMtok", 0), cheapest.get("outputINRPerMtok", 0)
    return 0.0, 0.0


model = pick_model()
stream = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "Write a two-line haiku about Bengaluru traffic."}],
    stream=True,
    stream_options={"include_usage": True},
)

usage = None
for chunk in stream:
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
    if chunk.usage:
        usage = chunk.usage
print()

if usage:
    in_rate, out_rate = inr_rates(model)
    cost = usage.prompt_tokens / 1e6 * in_rate + usage.completion_tokens / 1e6 * out_rate
    print(f"\ntokens: {usage.prompt_tokens} in / {usage.completion_tokens} out  →  ₹{cost:.6f}")
