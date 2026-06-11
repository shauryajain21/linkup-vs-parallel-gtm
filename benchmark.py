import argparse, asyncio, json, os
from dataclasses import dataclass

import anthropic, httpx
from rich.console import Console
from rich.table import Table

console = Console()
LINKUP_KEY   = os.environ["LINKUP_API_KEY"]
PARALLEL_KEY = os.environ["PARALLEL_API_KEY"]
ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]
SYNTH_MODEL = "claude-opus-4-8"
JUDGE_MODEL = "claude-fable-5"

DIMS = ["accuracy","completeness","gtm_value","specificity","source_quality","signal_to_noise"]


def _text(resp):
    if not resp.content: return ""
    for b in resp.content:
        if getattr(b, "text", None): return b.text
    return ""


async def linkup_search(client, query, sem):
    async with sem:
        for a in range(4):
            try:
                r = await client.post("https://api.linkup.so/v1/search",
                    headers={"Authorization": f"Bearer {LINKUP_KEY}", "Content-Type":"application/json"},
                    json={"q": query, "depth":"standard", "outputType":"searchResults"}, timeout=60)
                r.raise_for_status()
                return [{"url":x.get("url",""), "title":x.get("name",""), "content":x.get("content","")}
                        for x in r.json().get("results", [])]
            except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.ReadError):
                await asyncio.sleep(2**a)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429: await asyncio.sleep(10*(a+1))
                else: return []
        return []


async def parallel_search(client, query, sem):
    async with sem:
        for a in range(4):
            try:
                r = await client.post("https://api.parallel.ai/v1beta/search",
                    headers={"x-api-key": PARALLEL_KEY, "Content-Type":"application/json",
                             "parallel-beta":"search-extract-2025-10-10"},
                    json={"objective": query, "max_results":10, "excerpts":{}}, timeout=60)
                r.raise_for_status()
                out=[]
                for x in r.json().get("results", []):
                    ex=x.get("excerpts", [])
                    out.append({"url":x.get("url",""), "title":x.get("title",""),
                                "content":"\n".join(ex) if isinstance(ex,list) else str(ex)})
                return out
            except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.ReadError):
                await asyncio.sleep(2**a)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429: await asyncio.sleep(10*(a+1))
                else: return []
        return []


SYNTH_SYSTEM = """You are a research assistant. Answer the user's question using ONLY the search results provided.
Be specific and factual. Cite concrete details (numbers, names, products) found in the sources.
If the sources don't contain the answer, say so. Do not use outside knowledge."""

async def synth(claude, query, results, sem):
    if not results: return ""
    src = "\n\n".join(f"[Source {i}] {r['title']} ({r['url']})\n{r['content']}" for i,r in enumerate(results,1))
    async with sem:
        for a in range(3):
            try:
                resp = await claude.messages.create(model=SYNTH_MODEL, max_tokens=600, system=SYNTH_SYSTEM,
                    messages=[{"role":"user","content":f"Question: {query}\n\nSearch results:\n{src}"}])
                return _text(resp).strip()
            except anthropic.RateLimitError: await asyncio.sleep(15*(a+1))
            except Exception: await asyncio.sleep(2**a)
        return ""


JUDGE_SYSTEM = """You are a GTM research quality evaluator. A sales team asked a question about a company
and received an answer synthesized from search results. Score the answer on 6 dimensions (0-10).

- accuracy: factually grounded and about the right company/entity?
- completeness: fully addresses everything the question asked?
- gtm_value: actionable for a sales/GTM professional?
- specificity: concrete details (numbers, names, products, dates) vs vague generalities?
- source_quality: are the cited sources authoritative and on-target (the company's own site,
  official pages, reputable sources) rather than random/irrelevant pages?
- signal_to_noise: dense with relevant info, or padded with boilerplate, hedging, and filler?

Calibration: 9-10 = excellent, 7-8 = good, 5-6 = basic/vague, 0-4 = wrong/empty/"sources don't contain the answer".
Return ONLY valid JSON: {"accuracy":<0-10>,"completeness":<0-10>,"gtm_value":<0-10>,"specificity":<0-10>,"source_quality":<0-10>,"signal_to_noise":<0-10>,"reason":"<one sentence>"}"""

@dataclass
class Grade:
    accuracy:float=0; completeness:float=0; gtm_value:float=0
    specificity:float=0; source_quality:float=0; signal_to_noise:float=0; reason:str=""
    @property
    def total(self): return sum(getattr(self,d) for d in DIMS)/6

async def judge(claude, query, answer, sem):
    if not answer or len(answer) < 20: return Grade(reason="empty")
    async with sem:
        for a in range(3):
            try:
                resp = await claude.messages.create(model=JUDGE_MODEL, max_tokens=2000, system=JUDGE_SYSTEM,
                    messages=[{"role":"user","content":f"Question: {query}\n\nAnswer: {answer}"}])
                raw = _text(resp).strip()
                if not raw: await asyncio.sleep(2**a); continue
                if "```" in raw:
                    for p in raw.split("```"):
                        p=p.strip().lstrip("json").strip()
                        if p.startswith("{"): raw=p; break
                d = json.loads(raw)
                return Grade(*[float(d.get(k,0)) for k in DIMS], reason=str(d.get("reason","")))
            except (json.JSONDecodeError, KeyError, ValueError): await asyncio.sleep(2**a)
            except anthropic.RateLimitError: await asyncio.sleep(15*(a+1))
            except Exception: break
    return Grade(reason="judge failed")


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--concurrency", type=int, default=12)
    ap.add_argument("--out", default="results/results.json")
    args = ap.parse_args()

    queries = [json.loads(l) for l in open(args.input) if l.strip()]
    console.print(f"\n[bold]Linkup vs Parallel — GTM Benchmark[/bold]  ({len(queries)} queries)")
    console.print(f"  Retrieval: Linkup Search (standard) vs Parallel Search")
    console.print(f"  Synthesizer: {SYNTH_MODEL} (shared) | Judge: {JUDGE_MODEL} (independent)\n")

    lk_sem = asyncio.Semaphore(args.concurrency)
    pl_sem = asyncio.Semaphore(min(args.concurrency, 9))
    synth_sem = asyncio.Semaphore(12); judge_sem = asyncio.Semaphore(12)
    claude = anthropic.AsyncAnthropic(api_key=ANTHROPIC_KEY)
    rows = []

    async def proc(q):
        async with httpx.AsyncClient() as c:
            lk, pl = await asyncio.gather(linkup_search(c,q["query"],lk_sem),
                                          parallel_search(c,q["query"],pl_sem))
        la, pa = await asyncio.gather(synth(claude,q["query"],lk,synth_sem),
                                      synth(claude,q["query"],pl,synth_sem))
        lg, pg = await asyncio.gather(judge(claude,q["query"],la,judge_sem),
                                      judge(claude,q["query"],pa,judge_sem))
        rows.append({"id":q["id"], "category":q.get("category",""),
                     "linkup":lg.__dict__, "parallel":pg.__dict__,
                     "linkup_total":round(lg.total,2), "parallel_total":round(pg.total,2)})
        if len(rows)%20==0: console.print(f"  {len(rows)}/{len(queries)}")

    CH=args.concurrency
    for i in range(0,len(queries),CH):
        await asyncio.gather(*[proc(q) for q in queries[i:i+CH]])

    n=len(rows)
    t=Table(title=f"Results — {n} GTM queries")
    t.add_column("Dimension", style="cyan"); t.add_column("Linkup", justify="right"); t.add_column("Parallel", justify="right")
    for d in DIMS:
        l=sum(r['linkup'][d] for r in rows)/n; p=sum(r['parallel'][d] for r in rows)/n
        t.add_row(d.replace("_"," ").title(), f"{l:.1f}", f"{p:.1f}")
    lt=sum(r['linkup_total'] for r in rows)/n; pt=sum(r['parallel_total'] for r in rows)/n
    w=sum(1 for r in rows if r['linkup_total']>=r['parallel_total'])
    t.add_section(); t.add_row("TOTAL", f"{lt:.1f}", f"{pt:.1f}")
    t.add_row("Win rate", f"{w}/{n}", f"{n-w}/{n}")
    console.print(t)
    json.dump(rows, open(args.out,"w"), indent=2)
    console.print(f"\n  saved → {args.out}")


if __name__ == "__main__":
    asyncio.run(main())
