<div align="center">
  <img src="assets/logo.svg" alt="BharatRouter" width="72" height="72" />
  <h1>BharatRouter Cookbook</h1>
  <p><strong>Runnable recipes for India's AI gateway.</strong><br/>
  One OpenAI-compatible API over many models — with enforceable India data-residency, INR billing, and price / latency / uptime routing across providers.</p>

  <a href="https://bharatrouter.com">Website</a> ·
  <a href="https://bharatrouter.com/cookbook">Cookbook (web)</a> ·
  <a href="https://bharatrouter.com/docs">Docs</a> ·
  <a href="https://bharatrouter.com/llms-full.txt">llms-full.txt</a>
</div>

---

Every folder in [`recipes/`](recipes/) is a **self-contained, runnable** companion to a recipe on the
[web cookbook](https://bharatrouter.com/cookbook). Clone, set one environment variable, run.

> The gateway speaks the **OpenAI wire format** (`/v1/chat/completions`), so these examples use the
> standard `openai` SDK with nothing more than a base-URL swap. The same code works in any
> OpenAI-compatible client.

## Quickstart

```bash
git clone https://github.com/bharatrouter/cookbook.git
cd cookbook

# 1. Get a key — sign up at https://bharatrouter.com/login (new orgs get ₹100 credit)
cp .env.example .env        # then put your br-... key in BHARATROUTER_API_KEY

# 2. Install deps and run any recipe
pip install -r requirements.txt
python recipes/01-cut-inference-costs/main.py
```

### Choosing a model

The recipes don't hard-code any provider. They read **`BHARATROUTER_MODEL`** if you set it,
otherwise they pick one from your live catalog (`GET /v1/models`). Browse the full catalog —
with INR pricing, residency and modalities — at **https://bharatrouter.com/models**, then:

```bash
export BHARATROUTER_MODEL=<any-model-id-from-the-catalog>
```

## Recipes

| # | Recipe | What it shows | Web |
|---|--------|---------------|-----|
| 01 | [Cut your inference bill](recipes/01-cut-inference-costs) | Cheapest eligible route by default with `optimize:price` | [↗](https://bharatrouter.com/cookbook/cut-inference-costs) |
| 02 | [Compare pricing (INR)](recipes/02-compare-pricing) | Live FX-converted price comparison per model | [↗](https://bharatrouter.com/cookbook/compare-openrouter) |
| 03 | [Never return an error](recipes/03-failover-chain) | Ordered fallback chain with circuit-breaker failover | [↗](https://bharatrouter.com/cookbook/failover-chain) |
| 04 | [Keep prompts in India](recipes/04-india-only) | `data_policy: "india_only"` — fail closed, never route offshore | [↗](https://bharatrouter.com/cookbook/india-only) |
| 05 | [Handle PII (DPDP)](recipes/05-dpdp-pii) | Residency + zero-retention + client-side redaction | [↗](https://bharatrouter.com/cookbook/dpdp-pii) |
| 06 | [Hindi / Indic chatbot](recipes/06-indic-chatbot) | Indian-language chat on India-resident routes | [↗](https://bharatrouter.com/cookbook/indic-models) |
| 07 | [Bring your own key](recipes/07-byok) | Ride your own provider account & rates via `upstream_key` | [↗](https://bharatrouter.com/cookbook/byok) |
| 08 | [Wire an agent (MCP)](recipes/08-mcp-agent) | Connect any MCP agent to one governed endpoint | [↗](https://bharatrouter.com/cookbook/mcp-agent) |
| 09 | [Stream tokens + exact ₹ cost](recipes/09-streaming-cost) | Streaming with per-call INR usage accounting | [↗](https://bharatrouter.com/cookbook/streaming-usage) |
| 10 | [Sangam consensus](recipes/10-sangam-consensus) | A panel answers in parallel; a synthesizer reconciles one best answer | [↗](https://bharatrouter.com/cookbook/sangam-consensus) |
| 11 | [Use Claude through BharatRouter](recipes/11-use-claude) | Call Claude on the platform key or via BYOK; wire Claude Code in as an MCP agent | [↗](https://bharatrouter.com/cookbook/claude-with-bharatrouter) |
| 12 | [Run a coding agent on GLM (one command)](recipes/12-glm-coding-agent) | One-command OpenCode + GLM-4.6 install — governed, metered, with a first query on launch | [↗](https://bharatrouter.com/blog/zero-to-glm) |

## BharatRouter-specific request fields

These ride on a normal chat-completions request and are stripped before forwarding upstream:

| Field | Meaning |
|-------|---------|
| `optimize` | `"price"` (default) `\| "latency" \| "uptime" \| "throughput" \| "auto"` — route-selection preference |
| `data_policy` | `"india_only"` — only India-resident routes are eligible (fail closed) |
| `open_weights` / `permissive` | restrict to open-weight / permissively-licensed models |
| `provider` | pin one provider and skip dynamic routing |
| `fallbacks` | per-request ordered `[{model, provider?}]` failover chain |
| `upstream_key` | per-request BYOK — your own provider key |

The provider that actually served a request is returned in the `x-br-provider` response header.

Full machine-readable reference: **https://bharatrouter.com/llms-full.txt**

## For agents (automatic use)

These recipes are written for humans to read and run — but an autonomous agent can discover and
use the gateway **without a human in the loop**, because every surface is machine-readable:

| Want to… | Fetch | Returns |
|----------|-------|---------|
| Discover the gateway | [`/llms.txt`](https://bharatrouter.com/llms.txt) | the agent-oriented index (API, extensions, MCP, **Cookbook**) |
| Read the full reference in one shot | [`/llms-full.txt`](https://bharatrouter.com/llms-full.txt) | endpoints, request fields, errors, **every recipe** with URLs |
| List callable models | [`GET /v1/models`](https://api.bharatrouter.com/v1/models) | catalog with INR pricing, residency, modalities, live health |
| Get the API contract | [`/openapi.json`](https://api.bharatrouter.com/openapi.json) | OpenAPI 3.1 schema |
| Drive it as a tool | `POST https://api.bharatrouter.com/mcp` | native **MCP server** (streamable HTTP, bearer key) |

A typical autonomous flow:

```text
GET /llms.txt            → learn the gateway exists, find the Cookbook + llms-full.txt
GET /llms-full.txt       → read the request fields (optimize, data_policy, fallbacks, …)
GET /v1/models           → pick a model id that fits (price / residency / modality)
POST /v1/chat/completions→ call it; read x-br-provider to confirm who served
```

Or skip HTTP entirely and connect over **MCP** — see [`recipes/08-mcp-agent`](recipes/08-mcp-agent),
which includes a drop-in [`mcp.json`](recipes/08-mcp-agent/mcp.json). The agent then discovers and
calls models as governed tools, inheriting your routing, residency and budgets on every step.

## Contributing

Recipes are intentionally small and dependency-light. To add one: create `recipes/NN-slug/` with a
`README.md` and a runnable `main.py`, then add a row to the table above.

## License

[MIT](LICENSE) — copy these freely into your own projects.
