# Stream tokens + exact ₹ cost

Stream the response, ask for usage in the final chunk, and price it in INR from the live catalog.

```bash
python recipes/09-streaming-cost/main.py
```

Reads `BHARATROUTER_API_KEY` from the environment and points at `https://api.bharatrouter.com/v1`.
Set `BHARATROUTER_MODEL` to any id from [the catalog](https://bharatrouter.com/models), or let the
recipe pick one for you.

**Web version:** https://bharatrouter.com/cookbook/streaming-usage
