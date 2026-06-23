"""Unlock more models with your own key (BYOK).

Pass your own upstream provider key per request via `upstream_key`. The call rides your
account and your rate limits, while BharatRouter still does routing, budgets and INR metering
on top. (You can also save a key once in the dashboard instead of sending it per request.)

Run: BHARATROUTER_MODEL=<id> BHARATROUTER_UPSTREAM_KEY=<your-provider-key> \
       python recipes/07-byok/main.py
"""
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

BASE = os.getenv("BHARATROUTER_BASE_URL", "https://api.bharatrouter.com/v1")
client = OpenAI(base_url=BASE, api_key=os.environ["BHARATROUTER_API_KEY"])

model = os.environ.get("BHARATROUTER_MODEL")
upstream = os.environ.get("BHARATROUTER_UPSTREAM_KEY")
if not model or not upstream:
    raise SystemExit(
        "Set BHARATROUTER_MODEL (the model your key unlocks) and BHARATROUTER_UPSTREAM_KEY "
        "(your own provider key) to run this recipe."
    )

resp = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "One-line release note for v0.6."}],
    extra_body={"upstream_key": upstream},
)
print("served by:", resp.model)
print(resp.choices[0].message.content)
