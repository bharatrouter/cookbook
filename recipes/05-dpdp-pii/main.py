"""Handle PII under India's DPDP Act.

Defence in depth for personal data:
  1. client-side redaction  — strip obvious PII before it ever leaves your process
  2. data_policy: india_only — keep processing on India-resident routes
  3. zero-retention          — inference is zero-retention by default on BharatRouter

Run: python recipes/05-dpdp-pii/main.py
"""
import os
import re
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


EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE = re.compile(r"\b(?:\+?91[-\s]?)?[6-9]\d{9}\b")


def redact(text: str) -> str:
    return PHONE.sub("[PHONE]", EMAIL.sub("[EMAIL]", text))


raw_ticket = "Customer Asha (asha@example.com, +91 98765 43210) wants a refund."
safe = redact(raw_ticket)
print("redacted:", safe)

resp = client.chat.completions.create(
    model=pick_model(),
    messages=[{"role": "user", "content": f"Summarise this support ticket in one line: {safe}"}],
    extra_body={"data_policy": "india_only"},
)
print(resp.choices[0].message.content)
