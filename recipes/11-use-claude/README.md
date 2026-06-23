# Use Claude through BharatRouter

Reach Anthropic's Claude over the gateway — on the platform key or your own Anthropic key — and
wire Claude Code in as an agent over MCP, with your routing, residency and budgets on every call.

```bash
python recipes/11-use-claude/main.py
```

## Part A — call Claude through the gateway

Claude is just another model id. Point your existing OpenAI code at the gateway and pass a Claude
model — no Anthropic SDK required.

**On the platform key** — `claude-haiku-4.5` is in the catalog today:

```python
resp = client.chat.completions.create(
    model="claude-haiku-4.5",
    messages=[{"role": "user", "content": "Summarise this ticket in one line: ..."}],
)
```

**Your own Anthropic key (BYOK)** — for the full lineup (`claude-opus-4-8`, `claude-sonnet-4-6`),
save your key once and call any discovered model with the `anthropic/` prefix:

```bash
curl -X PUT https://api.bharatrouter.com/me/byok/anthropic \
  -H "Authorization: Bearer br-..." \
  -d '{"key": "sk-ant-...", "label": "prod"}'
```

```python
resp = client.chat.completions.create(
    model="anthropic/claude-opus-4-8",
    messages=[{"role": "user", "content": "Draft a release note for v0.6."}],
)
```

> **Residency:** Anthropic is a global (US) provider, so a Claude call leaves India — it will
> **not** satisfy `data_policy: "india_only"`. For India-resident work, route an India-resident
> model and reserve Claude for calls where offshore is acceptable. See
> [recipe 04](../04-india-only).

## Part B — wire Claude Code as an agent (MCP)

Connect Claude Code to the gateway's MCP server and it can discover and call every model as a
governed tool, inheriting your routing and residency on each step:

```bash
claude mcp add --transport http bharatrouter \
  https://api.bharatrouter.com/mcp \
  --header "Authorization: Bearer br-..."
```

> **Why not just set `ANTHROPIC_BASE_URL`?** The gateway serves the OpenAI wire format and MCP —
> not the Anthropic Messages API (`/v1/messages`). Use the OpenAI SDK (Part A) to call Claude, or
> MCP (above) to govern the agent. See also [recipe 08](../08-mcp-agent).

**Web version:** https://bharatrouter.com/cookbook/claude-with-bharatrouter
