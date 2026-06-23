# Hindi / Indic chatbot

Serve Indian-language chat on India-resident routes; pick any Indic-capable model from the catalog.

```bash
python recipes/06-indic-chatbot/main.py
```

Reads `BHARATROUTER_API_KEY` from the environment and points at `https://api.bharatrouter.com/v1`.
Set `BHARATROUTER_MODEL` to any id from [the catalog](https://bharatrouter.com/models), or let the
recipe pick one for you.

**Web version:** https://bharatrouter.com/cookbook/indic-models
