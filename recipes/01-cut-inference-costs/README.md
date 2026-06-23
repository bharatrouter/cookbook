# Cut your inference bill

Default to the cheapest eligible route with `optimize:price` and delegate routine work to a smaller model.

```bash
python recipes/01-cut-inference-costs/main.py
```

Reads `BHARATROUTER_API_KEY` from the environment and points at `https://api.bharatrouter.com/v1`.
Set `BHARATROUTER_MODEL` to any id from [the catalog](https://bharatrouter.com/models), or let the
recipe pick one for you.

**Web version:** https://bharatrouter.com/cookbook/cut-inference-costs
