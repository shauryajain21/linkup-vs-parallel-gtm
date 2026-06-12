"""Retrieval latency benchmark: Linkup Search vs Parallel Search.

Clean latency measurement (retrieval only — no synthesis or judging, no concurrency).
For each query we call Linkup then Parallel back-to-back (interleaved) so both see the
same network conditions, timing only the search POST with time.monotonic(). Calls are
issued strictly sequentially so the two providers never contend for bandwidth.

Only first-attempt successful calls count toward the reported percentiles; retried or
failed calls are recorded and reported separately but excluded from the stats.

Usage:
    export LINKUP_API_KEY=...           # https://linkup.so
    export PARALLEL_API_KEY=...         # https://parallel.ai  (or PARALLEL_API_KEYS=k1,k2)
    python latency_benchmark.py                 # full run, all four benchmarks
    python latency_benchmark.py --fraction 0.5  # stratified 50% sample
"""
import argparse, json, os, random, statistics, time
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
LINKUP_KEY = os.environ["LINKUP_API_KEY"]
# Accept a single key (PARALLEL_API_KEY) or a comma-separated pool (PARALLEL_API_KEYS).
# A key that returns 402 (out of credit) is dropped and the next one is tried.
_pk = os.environ.get("PARALLEL_API_KEY") or os.environ["PARALLEL_API_KEYS"]
PARALLEL_KEYS = [k.strip() for k in _pk.split(",") if k.strip()]

BENCHMARKS = [
    ("company_research", "data/company_research_queries.jsonl"),
    ("signal",           "data/news_signal_queries.jsonl"),
    ("people_search",    "data/people_queries.jsonl"),
    ("people_research",  "data/coresignal_people_queries.jsonl"),
]


def linkup_call(client, query):
    """Returns (latency_s, status, attempts). Times only a clean first-attempt success."""
    for a in range(4):
        t0 = time.monotonic()
        try:
            r = client.post("https://api.linkup.so/v1/search",
                headers={"Authorization": f"Bearer {LINKUP_KEY}", "Content-Type": "application/json"},
                json={"q": query, "depth": "standard", "outputType": "searchResults"}, timeout=60)
            dt = time.monotonic() - t0
            r.raise_for_status()
            return round(dt, 3), "ok", a + 1
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                time.sleep(10 * (a + 1)); continue
            return round(time.monotonic() - t0, 3), f"http_{e.response.status_code}", a + 1
        except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.ReadError, httpx.ConnectError):
            time.sleep(2 ** a); continue
    return None, "failed", 4


def parallel_call(client, query):
    attempts = 0
    for a in range(4):
        if not PARALLEL_KEYS:
            return None, "no_credit", attempts
        key = PARALLEL_KEYS[0]
        attempts += 1
        t0 = time.monotonic()
        try:
            r = client.post("https://api.parallel.ai/v1beta/search",
                headers={"x-api-key": key, "Content-Type": "application/json",
                         "parallel-beta": "search-extract-2025-10-10"},
                json={"objective": query, "max_results": 10, "excerpts": {}}, timeout=60)
            dt = time.monotonic() - t0
            r.raise_for_status()
            PARALLEL_KEYS.append(PARALLEL_KEYS.pop(0))  # rotate to spread load
            return round(dt, 3), "ok", attempts
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 402:
                PARALLEL_KEYS.pop(0)  # drop exhausted key, retry with next
                continue
            if e.response.status_code == 429:
                time.sleep(10 * (a + 1)); continue
            return round(time.monotonic() - t0, 3), f"http_{e.response.status_code}", attempts
        except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.ReadError, httpx.ConnectError):
            time.sleep(2 ** a); continue
    return None, "failed", attempts


def pct(xs, p):
    if not xs: return None
    xs = sorted(xs)
    k = (len(xs) - 1) * (p / 100)
    lo, hi = int(k), min(int(k) + 1, len(xs) - 1)
    return round(xs[lo] + (xs[hi] - xs[lo]) * (k - lo), 3)


def summarize(xs):
    clean = [x for x in xs if x is not None]
    if not clean:
        return {"n": 0}
    return {"n": len(clean),
            "p50": pct(clean, 50), "p90": pct(clean, 90), "p95": pct(clean, 95), "p99": pct(clean, 99),
            "mean": round(statistics.mean(clean), 3),
            "min": round(min(clean), 3), "max": round(max(clean), 3)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fraction", type=float, default=1.0, help="stratified sample fraction (1.0 = all)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--rows", default="results/latency_rows.jsonl")
    ap.add_argument("--out", default="results/latency_results.json")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    rows_path = HERE / args.rows; rows_path.parent.mkdir(parents=True, exist_ok=True)

    sampled = []
    for bench, rel in BENCHMARKS:
        rows = [json.loads(l) for l in open(HERE / rel) if l.strip()]
        k = max(1, round(len(rows) * args.fraction))
        pick = rng.sample(rows, k) if k < len(rows) else rows
        for q in pick:
            sampled.append({"benchmark": bench, "id": q["id"], "query": q["query"]})
        print(f"{bench}: {k}/{len(rows)}", flush=True)
    # Shuffle so a provider running out of credit mid-run spreads the gap across benchmarks.
    rng.shuffle(sampled)
    print(f"TOTAL: {len(sampled)} queries ({len(sampled)*2} calls)\n", flush=True)

    rows = []
    fout = open(rows_path, "w")
    with httpx.Client() as client:
        try: linkup_call(client, "warmup")
        except Exception: pass
        try: parallel_call(client, "warmup")
        except Exception: pass

        t_start = time.monotonic()
        for i, q in enumerate(sampled, 1):
            lk_s, lk_status, lk_att = linkup_call(client, q["query"])
            pl_s, pl_status, pl_att = parallel_call(client, q["query"])
            row = {"benchmark": q["benchmark"], "id": q["id"],
                   "linkup_s": lk_s, "linkup_status": lk_status, "linkup_attempts": lk_att,
                   "parallel_s": pl_s, "parallel_status": pl_status, "parallel_attempts": pl_att}
            rows.append(row)
            fout.write(json.dumps(row) + "\n"); fout.flush()
            if i % 25 == 0 or i == len(sampled):
                print(f"  {i}/{len(sampled)}  (elapsed {(time.monotonic()-t_start)/60:.1f} min)", flush=True)
    fout.close()

    def clean(row, prov):
        return row[f"{prov}_s"] if row[f"{prov}_status"] == "ok" and row[f"{prov}_attempts"] == 1 else None

    summary = {"fraction": args.fraction, "seed": args.seed, "total_queries": len(rows), "by_benchmark": {}}
    benches = [b for b, _ in BENCHMARKS] + ["ALL"]
    for b in benches:
        sub = rows if b == "ALL" else [r for r in rows if r["benchmark"] == b]
        lk = [clean(r, "linkup") for r in sub]
        pl = [clean(r, "parallel") for r in sub]
        paired = [(clean(r, "linkup"), clean(r, "parallel")) for r in sub]
        paired = [(a, p) for a, p in paired if a is not None and p is not None]
        deltas = [p - a for a, p in paired]
        summary["by_benchmark"][b] = {
            "linkup": summarize(lk), "parallel": summarize(pl),
            "paired_n": len(paired), "linkup_faster": sum(1 for a, p in paired if a < p),
            "median_delta_parallel_minus_linkup": pct(deltas, 50) if deltas else None,
            "dropped": {"linkup": sum(1 for x in lk if x is None), "parallel": sum(1 for x in pl if x is None)},
        }
    json.dump(summary, open(HERE / args.out, "w"), indent=2)

    def f(d, key):
        return f"{d[key]:>7}" if d.get("n", 0) and d.get(key) is not None else f"{'-':>7}"
    print("\n===== LATENCY (clean first-attempt successes, seconds) =====")
    hdr = f"{'benchmark':18} {'n LK/PL':>9}  {'LK p50':>7} {'PL p50':>7}  {'LK p90':>7} {'PL p90':>7}  {'LK avg':>7} {'PL avg':>7}"
    print(hdr); print("-" * len(hdr))
    for b in benches:
        s = summary["by_benchmark"][b]; lk, pl = s["linkup"], s["parallel"]
        if lk.get("n", 0) == 0 and pl.get("n", 0) == 0: continue
        print(f"{b:18} {str(lk.get('n',0))+'/'+str(pl.get('n',0)):>9}  "
              f"{f(lk,'p50')} {f(pl,'p50')}  {f(lk,'p90')} {f(pl,'p90')}  {f(lk,'mean')} {f(pl,'mean')}")
    print(f"\nsaved rows    -> {args.rows}")
    print(f"saved summary -> {args.out}")


if __name__ == "__main__":
    main()
