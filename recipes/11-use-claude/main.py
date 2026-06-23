"""Use Claude through BharatRouter.

Claude is just another model id on the gateway — call it with the standard OpenAI SDK and a
base-URL swap, no Anthropic SDK required. `claude-haiku-4.5` is available on the platform key;
the full Claude lineup is reachable with your own Anthropic key via BYOK (anthropic/<model>).

Run: python recipes/11-use-claude/main.py
"""
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url=os.getenv("BHARATROUTER_BASE_URL", "https://api.bharatrouter.com/v1"),
    api_key=os.environ["BHARATROUTER_API_KEY"],
)

# On the platform key — no Anthropic key needed.
resp = client.chat.completions.create(
    model="claude-haiku-4.5",
    messages=[{"role": "user", "content": "Summarise this ticket in one line: login fails after a password reset."}],
)
print(f"[{resp.model}] {resp.choices[0].message.content}")

# Want the full Claude lineup (e.g. claude-opus-4-8)? Save your own Anthropic key once via
# BYOK (https://bharatrouter.com/docs/byok), then call any discovered model with the
# anthropic/ prefix — same client, just a different model id:
#
#   resp = client.chat.completions.create(
#       model="anthropic/claude-opus-4-8",
#       messages=[{"role": "user", "content": "Draft a release note for v0.6."}],
#   )
