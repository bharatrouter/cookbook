# Compare pricing (INR)

Pull a live, FX-converted INR price comparison for a model straight from the gateway.

```bash
BHARATROUTER_MODEL=<id> python recipes/02-compare-pricing/main.py
```

Reads `BHARATROUTER_API_KEY` from the environment and points at `https://api.bharatrouter.com/v1`.
Set `BHARATROUTER_MODEL` to any id from [the catalog](https://bharatrouter.com/models), or let the
recipe pick one for you.

**Web version:** https://bharatrouter.com/cookbook/compare-openrouter
