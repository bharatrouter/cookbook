# Bring your own key (BYOK)

Pass your own provider key per request via `upstream_key` to ride your account and rates.

```bash
BHARATROUTER_MODEL=<id> BHARATROUTER_UPSTREAM_KEY=<key> python recipes/07-byok/main.py
```

Reads `BHARATROUTER_API_KEY` from the environment and points at `https://api.bharatrouter.com/v1`.
Set `BHARATROUTER_MODEL` to any id from [the catalog](https://bharatrouter.com/models), or let the
recipe pick one for you.

**Web version:** https://bharatrouter.com/cookbook/byok
