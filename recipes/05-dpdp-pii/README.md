# Handle PII under the DPDP Act

Combine client-side redaction, India residency and zero-retention to process personal data responsibly.

```bash
python recipes/05-dpdp-pii/main.py
```

Reads `BHARATROUTER_API_KEY` from the environment and points at `https://api.bharatrouter.com/v1`.
Set `BHARATROUTER_MODEL` to any id from [the catalog](https://bharatrouter.com/models), or let the
recipe pick one for you.

**Web version:** https://bharatrouter.com/cookbook/dpdp-pii
