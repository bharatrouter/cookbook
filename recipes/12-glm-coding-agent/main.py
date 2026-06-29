"""Run a coding agent on GLM through BharatRouter.

This recipe drives the open-source OpenCode harness with GLM-4.6 as the brain, all
governed through BharatRouter — see setup.sh / setup.ps1 for the one-command install.

main.py shows the call the agent makes under the hood: GLM-4.6 over the standard
OpenAI SDK with a base-URL swap. Run it to confirm your key routes GLM before you
launch the full tool-calling agent.

Run: python recipes/12-glm-coding-agent/main.py
"""
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url=os.getenv("BHARATROUTER_BASE_URL", "https://api.bharatrouter.com/v1"),
    api_key=os.environ["BHARATROUTER_API_KEY"],
)

# GLM is MIT-licensed and tuned for agentic coding. Swap to glm-4.5-air (cheap) or
# glm-4.7-flash (cheapest) by setting BHARATROUTER_MODEL.
model = os.getenv("BHARATROUTER_MODEL", "glm-4.6")

resp = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": (
        "In about 6 lines: roughly how much can a team save on coding-agent token "
        "costs by using GLM-4.6 instead of a frontier model (e.g. Claude Opus / "
        "GPT-4-class)? Use approximate public per-million-token input/output prices, "
        "show the comparison, and give a ballpark % saving."
    )}],
)
print(f"[{resp.model}] {resp.choices[0].message.content}")

# That's just the brain. To drive a full tool-calling coding agent on it, run the
# one-command installer (it installs OpenCode, handles keys, and runs a first query):
#
#   curl -fsSL https://bharatrouter.com/install/glm.sh | bash     # macOS / Linux
#   irm https://bharatrouter.com/install/glm.ps1 | iex            # Windows
#
# then, from any shell:
#
#   oc-glm run --model bharatrouter/glm-4.6 "Create fib.py and run it to print fib(10)."
