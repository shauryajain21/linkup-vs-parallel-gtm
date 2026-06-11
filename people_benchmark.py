import argparse, asyncio, json, os
from collections import defaultdict
import anthropic, httpx
from rich.console import Console
from rich.table import Table

console = Console()
LINKUP_KEY=os.environ["LINKUP_API_KEY"]; PARALLEL_KEY=os.environ["PARALLEL_API_KEY"]
ANTHROPIC_KEY=os.environ["ANTHROPIC_API_KEY"]
JUDGE_MODEL="claude-fable-5"; JUDGE_MAX_TOKENS=8000

def extract_text(resp):
    if not resp.content: return ""
    for b in resp.content:
        if getattr(b,"text",None): return b.text
    return ""
def is_profile(u): return "linkedin.com/in/" in (u or "")

PEOPLE_PROMPT=("Find LinkedIn personal profiles (linkedin.com/in/ URLs) of real people who currently "
               "match this description: {q}. Return only personal profile pages of distinct individuals — "
               "no job listings, company pages, or posts.")

async def linkup_people(client,q,sem):
    async with sem:
        for a in range(4):
            try:
                r=await client.post("https://api.linkup.so/v1/search",
                    headers={"Authorization":f"Bearer {LINKUP_KEY}","Content-Type":"application/json"},
                    json={"q":PEOPLE_PROMPT.format(q=q),"depth":"deep","outputType":"searchResults"},timeout=120)
                r.raise_for_status()
                return ([{"url":x.get("url",""),"title":x.get("name",""),"content":x.get("content","")}
                         for x in r.json().get("results",[]) if is_profile(x.get("url",""))], True)
            except (httpx.ReadTimeout,httpx.ConnectTimeout,httpx.ReadError): await asyncio.sleep(2**a)
            except httpx.HTTPStatusError as e:
                if e.response.status_code==429: await asyncio.sleep(10*(a+1))
                else: return ([],False)
        return ([],False)

async def parallel_people(client,q,sem):
    obj=f"Find LinkedIn personal profiles of people who are: {q}"
    async with sem:
        for a in range(4):
            try:
                r=await client.post("https://api.parallel.ai/v1beta/search",
                    headers={"x-api-key":PARALLEL_KEY,"Content-Type":"application/json",
                             "parallel-beta":"search-extract-2025-10-10"},
                    json={"objective":obj,"max_results":15,"excerpts":{},
                          "source_policy":{"include_domains":["linkedin.com"]}},timeout=120)
                r.raise_for_status()
                out=[]
                for x in r.json().get("results",[]):
                    if not is_profile(x.get("url","")): continue
                    ex=x.get("excerpts",[])
                    out.append({"url":x.get("url",""),"title":x.get("title",""),
                                "content":"\n".join(ex) if isinstance(ex,list) else str(ex)})
                return (out,True)
            except (httpx.ReadTimeout,httpx.ConnectTimeout,httpx.ReadError): await asyncio.sleep(2**a)
            except httpx.HTTPStatusError as e:
                if e.response.status_code==429: await asyncio.sleep(10*(a+1))
                else: return ([],False)
        return ([],False)

JUDGE_SYSTEM="""You evaluate a single LinkedIn profile result against a GTM people-search query.
Score with GRADED relevance and an outreach-readiness flag. Be reasonable: accept role equivalents
(Head/Director/VP of X are leadership-equivalent), same-metro for location; if the query omits a
dimension treat it as satisfied.

Return ONLY JSON:
{"grade":0|1|2|3, "reason":"<one sentence>"}

grade: 3 = exact fit (right function AND seniority AND location), 2 = right person, minor mismatch
(seniority or geo slightly off), 1 = real person but wrong function/role, 0 = not a real personal profile."""

async def judge_result(claude,query,result,sem):
    content=(result.get("content") or "")[:6000]
    user=f"Query: {query}\nURL: {result.get('url','')}\nTitle: {result.get('title','')}\n\nProfile content:\n{content}"
    async with sem:
        for a in range(3):
            try:
                resp=await claude.messages.create(model=JUDGE_MODEL,max_tokens=JUDGE_MAX_TOKENS,
                    system=JUDGE_SYSTEM,messages=[{"role":"user","content":user}])
                raw=extract_text(resp).strip()
                if not raw: await asyncio.sleep(2**a); continue
                if "```" in raw:
                    for p in raw.split("```"):
                        p=p.strip().lstrip("json").strip()
                        if p.startswith("{"): raw=p; break
                d=json.loads(raw)
                return {"grade":int(d.get("grade",0))}
            except (json.JSONDecodeError,KeyError,ValueError): await asyncio.sleep(2**a)
            except anthropic.RateLimitError: await asyncio.sleep(15*(a+1))
            except Exception: break
    return None

async def main():
    ap=argparse.ArgumentParser(); ap.add_argument("input"); ap.add_argument("--limit",type=int)
    ap.add_argument("--num",type=int,default=10); ap.add_argument("--concurrency",type=int,default=12)
    args=ap.parse_args()
    queries=[json.loads(l) for l in open(args.input) if l.strip()]
    if args.limit: queries=queries[:args.limit]
    console.print(f"\n[bold]Linkup GTM Prospecting Benchmark — {len(queries)} queries[/bold]")
    console.print("  Linkup vs Parallel (both best people config, /in/-filtered) | graded relevance | judge=Fable 5\n")

    lk_sem=asyncio.Semaphore(args.concurrency); pl_sem=asyncio.Semaphore(9); jsem=asyncio.Semaphore(12)
    claude=anthropic.AsyncAnthropic(api_key=ANTHROPIC_KEY)
    rows=[]; excluded=[]

    async def score(query,results):
        results=results[:args.num]
        if not results: return {"quality":0,"tophit":0,"n":0}
        g=await asyncio.gather(*[judge_result(claude,query,r,jsem) for r in results])
        if any(x is None for x in g): return None
        grades=[x["grade"] for x in g]
        return {"quality":sum(grades)/(3*len(grades)), "tophit":1 if grades[0]>=2 else 0, "n":len(results)}

    async def proc(q):
        async with httpx.AsyncClient() as c:
            (lk,lk_ok),(pl,pl_ok)=await asyncio.gather(linkup_people(c,q["query"],lk_sem),
                                                       parallel_people(c,q["query"],pl_sem))
        if not lk_ok or not pl_ok: excluded.append({"id":q["id"],"reason":"retrieval"}); return
        ls,ps=await asyncio.gather(score(q["query"],lk),score(q["query"],pl))
        if ls is None or ps is None: excluded.append({"id":q["id"],"reason":"judge"}); return
        rows.append({"id":q["id"],"segment":q.get("segment",""),"linkup":ls,"parallel":ps})
        console.print(f"  {len(rows)}/{len(queries)}")

    await asyncio.gather(*[proc(q) for q in queries])
    n=len(rows)
    if not n: console.print("[red]all excluded[/red]"); return

    def agg(side,key,subset=None):
        rs=subset or rows; return sum(r[side][key] for r in rs)/len(rs)

    t=Table(title=f"GTM Prospecting Benchmark — overall (scored {n}, excluded {len(excluded)})")
    t.add_column("Metric",style="cyan"); t.add_column("Linkup",justify="right"); t.add_column("Parallel",justify="right")
    t.add_row("Quality Score", f"{agg('linkup','quality'):.0%}", f"{agg('parallel','quality'):.0%}")
    t.add_row("Top-Result Hit", f"{agg('linkup','tophit'):.0%}", f"{agg('parallel','tophit'):.0%}")
    console.print(t)


    segs=sorted(set(r["segment"] for r in rows))
    t2=Table(title="Top-Result Hit by GTM persona")
    t2.add_column("Segment",style="cyan"); t2.add_column("Linkup",justify="right"); t2.add_column("Parallel",justify="right"); t2.add_column("n",justify="right")
    for s in segs:
        sub=[r for r in rows if r["segment"]==s]
        t2.add_row(s, f"{agg('linkup','tophit',sub):.0%}", f"{agg('parallel','tophit',sub):.0%}", str(len(sub)))
    console.print(t2)

    json.dump({"rows":rows,"excluded":excluded}, open("results/people_results.json","w"), indent=2)
    console.print("  saved → results/people_results.json")

if __name__=="__main__":
    asyncio.run(main())
