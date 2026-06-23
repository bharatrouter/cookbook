"""Wire an agent to one governed endpoint.

BharatRouter ships a native MCP server (see mcp.json in this folder) so any MCP-capable agent
can discover and call models through one governed endpoint — inheriting your routing, residency
and budgets on every step.

This script shows the same idea over the plain HTTP API: a minimal tool-calling loop where the
model decides to call a local tool. Model is resolved from the catalog (no hard-coded vendor).

Run: python recipes/08-mcp-agent/main.py
"""
import json
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


def order_status(order_id: str) -> str:
    """A toy local tool the agent can call."""
    return json.dumps({"order_id": order_id, "status": "out_for_delivery", "eta_days": 1})


TOOLS = [{
    "type": "function",
    "function": {
        "name": "order_status",
        "description": "Look up the delivery status of an order by id.",
        "parameters": {
            "type": "object",
            "properties": {"order_id": {"type": "string"}},
            "required": ["order_id"],
        },
    },
}]

model = pick_model()
messages = [{"role": "user", "content": "Where is order A1234? Answer in one line."}]

first = client.chat.completions.create(model=model, messages=messages, tools=TOOLS)
call = first.choices[0].message.tool_calls[0]
args = json.loads(call.function.arguments)
result = order_status(**args)

messages += [
    first.choices[0].message,
    {"role": "tool", "tool_call_id": call.id, "content": result},
]
final = client.chat.completions.create(model=model, messages=messages, tools=TOOLS)
print(final.choices[0].message.content)
