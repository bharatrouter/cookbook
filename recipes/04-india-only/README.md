# Keep prompts in India

Pin `data_policy: "india_only"` so requests fail closed rather than silently routing offshore.

```bash
python recipes/04-india-only/main.py
```

Reads `BHARATROUTER_API_KEY` from the environment and points at `https://api.bharatrouter.com/v1`.
Set `BHARATROUTER_MODEL` to any id from [the catalog](https://bharatrouter.com/models), or let the
recipe pick one for you.

**Web version:** https://bharatrouter.com/cookbook/india-only
