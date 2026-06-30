#!/usr/bin/env python3
"""
Blog 4 — host benchmark: the SAME GLM model on Baseten vs Zhipu vs OpenRouter,
all routed through BharatRouter (apples-to-apples). Measures, per (model, host):
  TTFT  — time to first token (streaming)         [vLLM prefill; MLPerf TTFT]
  lat   — total wall-clock to last token
  tput  — throughput = completion_tokens / generation_time (tok/s)  [decode phase]
  cost  — ₹/$ from token counts × that host's dated price (prices.md), FX ₹96/$
  errs  — failed/timed-out/429 calls (reliability axis)

Keys from env only (never disk): BR_API_KEY (Baseten+Zhipu BYOK on the org),
OPENROUTER_KEY (per-request upstream_key for the OpenRouter pin).

REPLICATE:
  export BR_API_KEY=br-... OPENROUTER_KEY=sk-or-v1-...
  REPEATS_HOST=30 python3 bench_hosts.py
"""
import json, os, ssl, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

BR_KEY = os.environ.get("BR_API_KEY", "")
OR_KEY = os.environ.get("OPENROUTER_KEY", "")
BR_BASE = os.environ.get("BR_BASE_URL", "https://api.bharatrouter.com")
REPEATS = int(os.environ.get("REPEATS_HOST", "30"))
WORKERS = int(os.environ.get("WORKERS_HOST", "2"))  # gentle: Baseten GLM-4.7 is RPM-15
FX = 96
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
HERE = os.path.dirname(os.path.abspath(__file__))

# A prompt that forces a few hundred output tokens so throughput is measurable.
PROMPT = ("Write a thread-safe LRU cache in Python as a class `LRUCache` with `get(key)` "
          "and `put(key, value, /)` (capacity in __init__). Include full docstrings, type hints, "
          "and three short usage examples. Return one Python code block.")

# ₹/Mtok (in, out) per host, dated (prices.md). Same model, different host = different rate.
PRICE = {
    ("glm-4.7", "baseten"):    (58, 211),   ("glm-4.7", "zhipu"):    (58, 211),   ("glm-4.7", "openrouter"):    (38, 168),
    ("glm-5.2", "baseten"):    (134, 422),  ("glm-5.2", "zhipu"):    (134, 422),  ("glm-5.2", "openrouter"):    (134, 422),
}
MATRIX = [("glm-4.7", h) for h in ("baseten", "zhipu", "openrouter")] + \
         [("glm-5.2", h) for h in ("baseten", "zhipu", "openrouter")]


def stream_once(model, host):
    body = {"model": model, "provider": host, "stream": True, "max_tokens": 700,
            "stream_options": {"include_usage": True},
            "messages": [{"role": "user", "content": PROMPT}]}
    if host == "openrouter":
        body["upstream_key"] = OR_KEY
    data = json.dumps(body).encode()
    headers = {"Authorization": f"Bearer {BR_KEY}", "Content-Type": "application/json",
               "Accept": "text/event-stream", "User-Agent": UA}
    req = urllib.request.Request(f"{BR_BASE}/v1/chat/completions", data=data, headers=headers, method="POST")
    t0 = time.time(); ttft = None; ctok = 0; ptok = 0; chunks = 0
    with urllib.request.urlopen(req, timeout=180, context=ssl.create_default_context()) as resp:
        for raw in resp:
            line = raw.decode("utf-8", "ignore").strip()
            if not line.startswith("data:"):
                continue
            payload = line[5:].strip()
            if payload == "[DONE]":
                break
            try:
                j = json.loads(payload)
            except Exception:
                continue
            ch = (j.get("choices") or [{}])[0]
            delta = ch.get("delta", {})
            if delta.get("content"):
                if ttft is None:
                    ttft = time.time() - t0
                chunks += 1
            if j.get("usage"):
                ptok = j["usage"].get("prompt_tokens", ptok)
                ctok = j["usage"].get("completion_tokens", ctok)
    total = time.time() - t0
    if ttft is None:
        ttft = total
    if not ctok:
        ctok = chunks  # fallback: 1 token≈1 chunk if usage absent
    gen = max(1e-6, total - ttft)
    return {"ttft": ttft, "lat": total, "tput": ctok / gen, "ctok": ctok, "ptok": ptok}


def run_cell(model, host):
    rows, errs = [], 0
    def one(_):
        delay = 4
        for attempt in range(5):
            try:
                return stream_once(model, host)
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt < 4:
                    time.sleep(delay); delay = min(delay * 2, 60); continue
                return {"err": f"HTTP {e.code}"}
            except Exception as e:
                if attempt < 4:
                    time.sleep(3); continue
                return {"err": str(e)[:80]}
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for f in as_completed([ex.submit(one, i) for i in range(REPEATS)]):
            r = f.result()
            if "err" in r:
                errs += 1
            else:
                rows.append(r)
    def med(key):
        xs = sorted(x[key] for x in rows)
        return xs[len(xs) // 2] if xs else 0.0
    pin, pout = PRICE[(model, host)]
    mean_in = sum(r["ptok"] for r in rows) / max(1, len(rows))
    mean_out = sum(r["ctok"] for r in rows) / max(1, len(rows))
    cost = mean_in * pin / 1e6 + mean_out * pout / 1e6
    return {"model": model, "host": host, "n": len(rows), "errors": errs,
            "ttft_med": round(med("ttft"), 3), "lat_med": round(med("lat"), 2),
            "tput_med": round(med("tput"), 1), "out_tok": round(mean_out),
            "inr": round(cost, 4), "usd": round(cost / FX, 5)}


def main():
    cells = MATRIX
    if len(sys.argv) > 1:  # optional filter: glm-4.7  or  baseten
        cells = [c for c in MATRIX if sys.argv[1] in c]
    print(f"host-bench repeats={REPEATS} workers={WORKERS} cells={cells}", file=sys.stderr)
    out = []
    for model, host in cells:
        print(f"\n=== {model} @ {host} (x{REPEATS}) ===", file=sys.stderr)
        r = run_cell(model, host)
        out.append(r)
        print(f"  TTFT={r['ttft_med']}s lat={r['lat_med']}s tput={r['tput_med']}tok/s "
              f"out={r['out_tok']} ₹{r['inr']}/${r['usd']} n={r['n']} errs={r['errors']}", file=sys.stderr)
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    json.dump(out, open(os.path.join(HERE, "results", "host-bench.json"), "w"), indent=2)
    print("WROTE results/host-bench.json")


if __name__ == "__main__":
    main()
