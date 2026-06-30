#!/usr/bin/env python3
"""
GLM-vs-Frontier reproducible benchmark — BharatRouter cookbook.

Compares open GLM models (single + Sangam consensus, via BharatRouter) against
frontier and budget models (OpenAI, Anthropic) on a set of execution-checked
coding tasks. Reports accuracy (pass-rate over N repeats), latency, and token
usage. Cost is computed separately (see prices.md) so the price sheet stays
auditable and dated.

REPLICATE:
  export BR_API_KEY=br-...            # BharatRouter key (https://bharatrouter.com)
  export OPENAI_API_KEY=sk-...        # only if you run OpenAI legs
  export ANTHROPIC_API_KEY=sk-ant-... # only if you run Anthropic legs
  TASKSET=all REPEATS=10 python3 benchmark.py opus gpt-5.5 glm-4.6 bharatrouter/glm-sangam

Keys are read from the environment only; nothing is written to disk except the
results JSON (model outputs, pass/fail, tokens, latency — never keys).
"""
import json, os, re, ssl, subprocess, sys, tempfile, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

BR_KEY = os.environ.get("BR_API_KEY", "")
OAI_KEY = os.environ.get("OPENAI_API_KEY", "")
ANT_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
BR_BASE = os.environ.get("BR_BASE_URL", "https://api.bharatrouter.com")

REPEATS = int(os.environ.get("REPEATS", "10"))
WORKERS = int(os.environ.get("WORKERS", "6"))
TASKSET = os.environ.get("TASKSET", "all")
HERE = os.path.dirname(os.path.abspath(__file__))
# A normal browser UA — BharatRouter's edge (Cloudflare) blocks default library UAs.
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

# leg -> upstream model id. Anything not in these maps is sent to BharatRouter as-is.
ANTHROPIC = {"opus": "claude-opus-4-8", "sonnet": "claude-sonnet-4-6", "haiku": "claude-haiku-4-5"}
OPENAI = {"gpt-5.5": "gpt-5.5", "gpt-5.4-mini": "gpt-5.4-mini", "gpt-5.4-nano": "gpt-5.4-nano"}

STANDARD = [
    ("is_prime", "Write a Python function `is_prime(n)` that returns True iff n is a prime number.",
     "assert is_prime(2) and is_prime(17) and is_prime(97)\nassert not is_prime(1) and not is_prime(18) and not is_prime(0)"),
    ("fib", "Write a Python function `fib(n)` returning the nth Fibonacci number, 0-indexed with fib(0)=0, fib(1)=1.",
     "assert fib(0)==0 and fib(1)==1 and fib(10)==55 and fib(20)==6765"),
    ("reverse_words", "Write a Python function `reverse_words(s)` that reverses the order of words in a string (single spaces).",
     "assert reverse_words('hello world')=='world hello'\nassert reverse_words('a b c')=='c b a'"),
    ("is_anagram", "Write a Python function `is_anagram(a, b)` returning True iff a and b are anagrams (case-sensitive).",
     "assert is_anagram('listen','silent') is True\nassert is_anagram('rat','car') is False"),
    ("binary_search", "Write a Python function `binary_search(arr, x)` for a sorted ascending list, returning the index of x or -1.",
     "assert binary_search([1,3,5,7,9],7)==3\nassert binary_search([1,3,5],4)==-1\nassert binary_search([],1)==-1"),
    ("roman_to_int", "Write a Python function `roman_to_int(s)` converting an uppercase Roman numeral to its integer value.",
     "assert roman_to_int('IV')==4 and roman_to_int('III')==3 and roman_to_int('MCMXCIV')==1994 and roman_to_int('LVIII')==58"),
    ("lcp", "Write a Python function `lcp(strs)` returning the longest common prefix of a list of strings ('' if none).",
     "assert lcp(['flower','flow','flight'])=='fl'\nassert lcp(['dog','car'])==''\nassert lcp(['abc'])=='abc'"),
    ("valid_parentheses", "Write a Python function `valid_parentheses(s)` returning True iff brackets ()[]{} are balanced and correctly nested.",
     "assert valid_parentheses('()[]{}') is True\nassert valid_parentheses('(]') is False\nassert valid_parentheses('([)]') is False\nassert valid_parentheses('{[]}') is True"),
]
HARD = [
    ("edit_distance", "Write a Python function `edit_distance(a, b)` returning the Levenshtein edit distance between two strings.",
     "assert edit_distance('horse','ros')==3\nassert edit_distance('intention','execution')==5\nassert edit_distance('','abc')==3 and edit_distance('abc','abc')==0"),
    ("coin_change", "Write a Python function `coin_change(coins, amount)` returning the fewest coins to make amount, or -1 if impossible.",
     "assert coin_change([1,2,5],11)==3\nassert coin_change([2],3)==-1\nassert coin_change([1],0)==0\nassert coin_change([186,419,83,408],6249)==20"),
    ("trap", "Write a Python function `trap(height)` returning units of rain water trapped given an elevation map (list of ints).",
     "assert trap([0,1,0,2,1,0,1,3,2,1,2,1])==6\nassert trap([4,2,0,3,2,5])==9\nassert trap([])==0"),
    ("word_break", "Write a Python function `word_break(s, words)` returning True iff s can be segmented into a sequence of one or more words from `words`.",
     "assert word_break('leetcode',['leet','code']) is True\nassert word_break('applepenapple',['apple','pen']) is True\nassert word_break('catsandog',['cats','dog','sand','and','cat']) is False"),
    ("regex_match", "Write a Python function `regex_match(s, p)` implementing regex matching with '.' (any char) and '*' (zero+ of preceding); must match the ENTIRE string.",
     "assert regex_match('aa','a') is False\nassert regex_match('aa','a*') is True\nassert regex_match('ab','.*') is True\nassert regex_match('mississippi','mis*is*p*.') is False\nassert regex_match('aab','c*a*b') is True"),
    ("min_window", "Write a Python function `min_window(s, t)` returning the minimum-length substring of s containing all chars of t (with multiplicity), or '' if none.",
     "assert min_window('ADOBECODEBANC','ABC')=='BANC'\nassert min_window('a','a')=='a'\nassert min_window('a','aa')==''"),
]
TASKS = STANDARD if TASKSET == "standard" else HARD if TASKSET == "hard" else STANDARD + HARD


def extract_code(text):
    m = re.findall(r"```(?:python)?\s*(.*?)```", text, re.DOTALL)
    return max(m, key=len) if m else text


def score(text, tests):
    src = extract_code(text) + "\n\n" + tests + "\nprint('PASS')\n"
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(src); path = f.name
    try:
        r = subprocess.run([sys.executable, path], capture_output=True, text=True, timeout=12)
        return r.returncode == 0 and "PASS" in r.stdout
    except Exception:
        return False
    finally:
        os.unlink(path)


def post(url, headers, payload, timeout=180):
    headers = {**headers, "User-Agent": UA, "Accept": "application/json", "Content-Type": "application/json"}
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as resp:
        return json.loads(resp.read().decode()), time.time() - t0


def call(leg, prompt):
    msgs = [{"role": "user", "content": prompt + "\nRespond with ONLY a single Python code block."}]
    if leg in ANTHROPIC:
        b, lat = post("https://api.anthropic.com/v1/messages",
                      {"x-api-key": ANT_KEY, "anthropic-version": "2023-06-01"},
                      {"model": ANTHROPIC[leg], "max_tokens": 4000, "messages": msgs})
        u = b.get("usage", {})
        return "".join(c.get("text", "") for c in b.get("content", [])), u.get("input_tokens", 0), u.get("output_tokens", 0), lat
    if leg in OPENAI:
        b, lat = post("https://api.openai.com/v1/chat/completions",
                      {"Authorization": f"Bearer {OAI_KEY}"},
                      {"model": OPENAI[leg], "max_completion_tokens": 4000, "messages": msgs})
        u = b.get("usage", {})
        return b["choices"][0]["message"]["content"], u.get("prompt_tokens", 0), u.get("completion_tokens", 0), lat
    body = {"model": leg, "max_tokens": 4000, "messages": msgs}
    or_key = os.environ.get("OPENROUTER_KEY")
    # Single open-model legs pinned to their FAST host (Baseten) — the real model on a
    # real serving host, no host handicap. All onboarded + slug-verified in the catalog.
    BASETEN = {"glm-4.7", "glm-5.2", "glm-5", "gpt-oss-120b", "nemotron-super",
               "nemotron-ultra", "kimi-k2.7-code", "kimi-k2.6", "kimi-k2.5", "deepseek-v4-pro"}
    if leg in BASETEN:
        body["provider"] = "baseten"
    elif or_key and leg in {"glm-4.6", "glm-4.5-air", "glm-4.7-flash"}:
        # Baseten doesn't serve these; route via OpenRouter BYOK (dodges Zhipu free-tier RPM cap).
        body["provider"] = "openrouter"
        body["upstream_key"] = or_key
    b, lat = post(f"{BR_BASE}/v1/chat/completions", {"Authorization": f"Bearer {BR_KEY}"}, body)
    u = b.get("usage", {})
    return b["choices"][0]["message"]["content"], u.get("prompt_tokens", 0), u.get("completion_tokens", 0), lat


def run_once(leg, task):
    name, prompt, tests = task
    # Backoff is env-tunable: a provider's per-model RPM (e.g. Baseten GLM-4.7) refills
    # fast, so a SHORT backoff + MANY attempts saturates the real limit and never DROPS a
    # call to a 429 (we have paid credits — retry through, don't give up).
    start = float(os.environ.get("BACKOFF_START", "5"))
    cap = float(os.environ.get("BACKOFF_CAP", "60"))
    attempts = int(os.environ.get("MAX_ATTEMPTS", "6"))
    delay = start
    for attempt in range(attempts):
        try:
            txt, pt, ct, lat = call(leg, prompt)
            return {"task": name, "ok": score(txt, tests), "ptok": pt, "ctok": ct, "lat": lat}
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < attempts - 1:
                time.sleep(delay); delay = min(delay * 2, cap); continue
            if attempt < attempts - 1:
                time.sleep(3); continue
            return {"task": name, "ok": False, "ptok": 0, "ctok": 0, "lat": 0.0, "err": f"HTTP {e.code}"}
        except Exception as e:
            if attempt < attempts - 1:
                time.sleep(3); continue
            return {"task": name, "ok": False, "ptok": 0, "ctok": 0, "lat": 0.0, "err": str(e)[:90]}


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else 0


def main():
    legs = sys.argv[1:] or ["opus", "gpt-5.5", "glm-4.6", "bharatrouter/glm-sangam"]
    outfile = os.path.join(HERE, "results", f"results-{TASKSET}-r{REPEATS}{os.environ.get('OUT_SUFFIX', '')}.json")
    os.makedirs(os.path.dirname(outfile), exist_ok=True)
    results = json.load(open(outfile)) if os.path.exists(outfile) else {}
    print(f"taskset={TASKSET} repeats={REPEATS} workers={WORKERS} tasks={len(TASKS)} legs={legs}", file=sys.stderr)
    for leg in legs:
        print(f"\n=== {leg} ({len(TASKS)} tasks x {REPEATS}) ===", file=sys.stderr)
        jobs = [task for task in TASKS for _ in range(REPEATS)]
        rows = []
        # Native APIs tolerate concurrency; BharatRouter→Zhipu free tier rate-limits, so BR legs run low.
        workers = WORKERS if (leg in OPENAI or leg in ANTHROPIC) else int(os.environ.get("WORKERS_BR", "2"))
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(run_once, leg, task) for task in jobs]
            for f in as_completed(futs):
                rows.append(f.result())
        by = {}
        for r in rows:
            by.setdefault(r["task"], []).append(r)
        agg, tp, tr, errs = {}, 0, 0, 0
        for name, rs in by.items():
            p = sum(x["ok"] for x in rs); tp += p; tr += len(rs); errs += sum(1 for x in rs if x.get("err"))
            agg[name] = {"runs": len(rs), "passes": p, "pass_rate": round(p / len(rs), 3),
                         "mean_in": round(mean([x["ptok"] for x in rs])),
                         "mean_out": round(mean([x["ctok"] for x in rs])),
                         "mean_lat": round(mean([x["lat"] for x in rs]), 2)}
        # APPEND=1: ACCUMULATE this batch onto the leg's existing totals so N grows over time
        # (run N=50 today, +N=50 next week -> N=100; Wilson CIs just tighten). Token/latency
        # means are merged run-weighted. Lets us top up a blog's numbers without re-running.
        if os.environ.get("APPEND") == "1" and leg in results:
            prev = results[leg]
            for name, cur in agg.items():
                old = prev["tasks"].get(name)
                if not old:
                    continue
                R = old["runs"] + cur["runs"]
                cur["passes"] += old["passes"]
                for k in ("mean_in", "mean_out", "mean_lat"):
                    cur[k] = round((old[k] * old["runs"] + cur[k] * cur["runs"]) / R, 2 if k == "mean_lat" else 0)
                cur["mean_in"], cur["mean_out"] = int(cur["mean_in"]), int(cur["mean_out"])
                cur["runs"] = R
                cur["pass_rate"] = round(cur["passes"] / R, 3)
            tp += prev["tot_pass"]; tr += prev["tot_runs"]; errs += prev.get("errors", 0)
        results[leg] = {"taskset": TASKSET, "repeats": REPEATS, "n_tasks": len(TASKS),
                        "tot_pass": tp, "tot_runs": tr, "overall_pass_rate": round(tp / tr, 3), "errors": errs,
                        "mean_in_per_task": round(mean([t["mean_in"] for t in agg.values()])),
                        "mean_out_per_task": round(mean([t["mean_out"] for t in agg.values()])),
                        "mean_lat_per_task": round(mean([t["mean_lat"] for t in agg.values()]), 2),
                        "tasks": agg}
        json.dump(results, open(outfile, "w"), indent=2)
        print(f"  => {tp}/{tr} = {100*tp/tr:.1f}%  errs={errs}  out/task={results[leg]['mean_out_per_task']} "
              f"lat/task={results[leg]['mean_lat_per_task']}s", file=sys.stderr)
    print("WROTE", outfile)


if __name__ == "__main__":
    main()
