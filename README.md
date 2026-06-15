# Linkup Search vs Parallel Search — GTM Retrieval Benchmarks

A suite of reproducible benchmarks comparing **Linkup Search** and **Parallel Search** across the GTM retrieval surface — the company-research, buying-signal, and people-search questions sales and growth teams run at scale. Every benchmark is designed so the **only variable is retrieval quality**: the same query goes to both APIs, the same downstream model turns each result set into an answer, and an independent model judges the answers blind.

Every benchmark compares the two products' **search APIs** (Linkup `/search`, Parallel `/search`) head-to-head.

## Benchmarks in this repo

| # | Benchmark | What it tests | Queries | Headline | Latency (avg) |
| --- | --- | --- | --- | --- | --- |
| 1 | **Company Research** | Enrichment & prospecting on a company | 250 | Linkup **7.3** vs Parallel 7.1 — leads 4 of 5 dimensions | Linkup **2.73s** vs Parallel 2.84s |
| 2 | **Signal** | Real-time GTM buying signals | 100 | Linkup **6.5** vs Parallel 6.3 | Linkup **1.91s** vs Parallel 2.72s |
| 3 | **People Search** | Right person's LinkedIn by role/seniority/location | 100 | Linkup **0.95** vs Parallel 0.91 nDCG@10 (73% vs 52% top-result hit) | Linkup **2.23s** vs Parallel 2.82s |
| 4 | **People Research** | Enrich / activity / signal for a named person (LinkedIn URL given) | 100 | Linkup **6.2** vs Parallel 5.9 — leads, enrichment-driven | Linkup **2.95s** vs Parallel 3.08s |

Details, methodology, and reproduce steps for each are below.

---

# 1. Company Research Benchmark

250 GTM company-research queries — the enrichment and prospecting questions sales/growth teams run at scale. Both APIs are tested at their comparable search tier and the same price point, and the answers are judged by an independent LLM (Claude Fable 5) on five GTM-relevant quality dimensions, scored 0–10.

## Results — 250 queries

| Dimension | Linkup | Parallel |
| --- | --- | --- |
| Accuracy | 8.3 | 8.3 |
| Completeness | **6.1** | 5.6 |
| GTM Value | **6.8** | 6.4 |
| Specificity | **7.8** | 7.7 |
| Signal-to-Noise | **7.5** | 7.4 |
| **Overall** | **7.3** | **7.1** |

**Linkup leads on four of five dimensions**, winning **138 / 250** queries head-to-head (15 ties).

### By query category

| Category | Linkup | Parallel | n |
| --- | --- | --- | --- |
| Company profile | **7.9** | 7.4 | 76 |
| Company enrichment | **7.5** | 7.1 | 63 |
| Company identification | **6.8** | 6.5 | 49 |
| Financial lookup | 6.6 | **6.8** | 36 |
| Website analysis | 7.6 | 7.6 | 25 |

Per-category rows cover 249 of 250 queries; 1 query in a miscellaneous `gtm_model` category is included in the overall score but omitted from this breakdown.

### Query selection

The 250 queries were randomly sampled from real Linkup production traffic — anonymized GTM company-research queries run by customers at scale. We filtered production logs to company-research intent (profile, enrichment, identification, financial lookup, website analysis), then drew a sample.

### Example queries

- **Company enrichment:** List every company logo in the "trusted by" / "our customers" sections on {company_url}.
- **Company profile:** What is the business activity of {company} (start from {company_url})? Focus on value-chain position, products/services, and end-markets.
- **Company identification:** What company operates {domain}? Common name, main product, recent news, notable customers, funding.
- **Financial lookup:** {company} annual revenue / EBITDA — official sources.
- **Website analysis:** Visit {company_url}; determine if the product is PLG (self-serve signup, free trial, public pricing, product access without sales).

---

# 2. Signal Benchmark

A separate run on **real-time GTM "buying signal" queries** — executive appointments, M&A, security-breach disclosures, and list-building roundups. These are the event-detection questions sales and security teams run for outbound timing: the trigger that says *reach out to this account now.* It uses the same pipeline as the company benchmark (identical query → shared Opus 4.8 synthesis → blind independent judge, Claude Opus 4.8).

## Results — 100 queries

| Dimension | Linkup | Parallel |
| --- | --- | --- |
| Accuracy | **6.4** | 5.9 |
| Completeness | **6.4** | 6.2 |
| GTM Value | **6.0** | 5.9 |
| Specificity | 7.5 | **7.6** |
| Signal-to-Noise | **6.2** | 6.0 |
| **Overall** | **6.5** | **6.3** |

Linkup leads on four of five dimensions. The two are closely matched on this workload overall, with Linkup's clearest edge on the largest categories.

### By signal category

| Category | Linkup | Parallel | n |
| --- | --- | --- | --- |
| Leadership change | **7.6** | 7.2 | 25 |
| M&A | **6.2** | 5.9 | 24 |
| Security / breach | **6.7** | 6.4 | 19 |
| List-building | 5.8 | 5.8 | 32 |

Linkup leads on **leadership-change**, **M&A**, and **security-breach** detection — the single-entity verification signals. **List-building** (broad sector roundups, the largest category) is a dead heat.

### Query selection

The 100 signal queries span four GTM buying-signal types — leadership changes, M&A, security breaches, and list-building roundups — phrased the way a sales or security vendor would run them for outreach timing. Most name a specific company and the facts to confirm (numbers, dates, root cause); the list-building queries ask for a roundup of recent events in a sector.

### Example queries

- **Leadership:** Verify a single leadership-change signal: Was Bo Berlas appointed CISO at CSBS (Conference of State Bank Supervisors) in 2026? Confirm exact title, announcement/effective date, prior role, and who they succeeded — with sources.
- **M&A:** Verify a single M&A signal: Did Blackstone and EQT agree to acquire Urbaser (environmental services, from Platinum Equity, ~$6.6B) in 2026? Confirm the deal structure, value, and announcement date with sources.
- **Security:** Verify a single security-incident signal: Did Change Healthcare disclose a ransomware breach in 2026 (reportedly ~192.7M records)? Confirm the number affected, data types, root cause, and disclosure dates — with source URLs.
- **List-building:** Are there any notable data breaches in the retail sector lately? Provide entities, details, and dates with source URLs.

---

# 3. People-Search Benchmark

100 GTM people-search / prospecting queries — finding the right person's LinkedIn profile by role, seniority, and location.

## Results — 100 queries

| Metric | Linkup | Parallel |
| --- | --- | --- |
| **nDCG@10** (overall ranking quality) | **0.95** | 0.91 |
| **MRR** (how high the right person ranks) | **0.78** | 0.68 |
| **Top-Result Hit (P@1)** | **73%** | 52% |
| Quality Score (mean relevance, top-10) | 57% | **60%** |

**Linkup ranks the right person higher; Parallel returns a slightly broader list.** Linkup leads every precision/ranking metric — nDCG@10, MRR, and Top-Result Hit — while Parallel edges mean relevance across the full top-10 (it casts a wider net). For outbound prospecting, where the job is the right person first, the ranking metrics are what matter.

### Configuration

Each product is run in its **own vendor-recommended configuration** for people search — Linkup with a people-targeting prompt, Parallel with a people objective and a LinkedIn source filter. Prompts are not transplanted between the two; each uses its native best-practice, which is how a team would actually deploy each API. Results from both are post-filtered to `linkedin.com/in/` profiles before grading.

### Top-Result Hit by GTM persona

| Segment | Linkup | Parallel |
| --- | --- | --- |
| Engineering | 80% | 70% |
| Marketing | 65% | 55% |
| Product | 85% | 50% |
| Ops / People | 65% | 30% |
| Revenue | 70% | 55% |

Linkup leads Top-Result Hit in **every** persona segment.

### What this measures

- **nDCG@10 / MRR / Top-Result Hit** reward precision — the right person ranked at or near the top. Linkup wins all three.
- **Quality Score** rewards relevance across the whole top-10 (breadth). Parallel a touch higher.

Read together: **Linkup is more precise at the top; Parallel returns a comparably relevant but broader list.** If "right person, first result" is what matters for outreach, Linkup leads.

### Example queries

- **Product:** product manager at AI startups in London
- **Revenue:** head of partnerships at B2B SaaS companies in Bangalore
- **Marketing:** director of demand generation at cybersecurity companies in San Francisco
- **Ops / People:** head of people in Singapore, 5+ years
- **Engineering:** staff engineer at developer-tools companies in Berlin

---

# 4. People-Research Benchmark

100 people-research queries about a *specific named individual* — lead enrichment, person-level signals (funding, job change), and recent public activity. Unlike benchmark 3 (which ranks *retrieval* of the right profile), this scores the *synthesized answer*: each API's raw results are passed to the same model and an independent model judges the answer. Each query provides the target's **LinkedIn URL** (identity is pinned), so it tests enrichment about a known person.

## Results — 100 queries

| Dimension | Linkup | Parallel |
| --- | --- | --- |
| Accuracy | 7.2 | **7.7** |
| Identity Match | **8.0** | 7.8 |
| Completeness | 4.5 | **4.6** |
| Recency | **5.6** | 4.5 |
| Specificity | **6.4** | 6.2 |
| GTM Value | **5.5** | 4.7 |
| **Overall** | **6.2** | **5.9** |

**Head-to-head: Linkup 60 · Parallel 30 · 10 ties.**

Linkup leads overall, driven by **enrichment** (the largest bucket) plus recency and GTM value. The ~0.3 overall gap is within run-to-run noise; the head-to-head split (60–30) and the enrichment-category win are the more reliable signals. Completeness is low for both — niche individuals are hard to fully enrich.

### Query selection

100 queries (enrichment 60 / activity 20 / signal 20), each naming a real individual with their LinkedIn URL.

### Example queries

- **Enrichment:** I'm enriching a sales lead: {name} (LinkedIn: {url}), listed as {title} at {company}. Confirm full name, current title/company, tenure, prior roles, education, location; note any discrepancy. Include source URLs and dates.
- **Activity:** Find recent public activity for {name} ({url}) — posts, articles, press, talks in the last several months, with dates.
- **Signal:** Check for a job-change or funding signal for {name} ({url}). Confirm what changed and when, with sources.

---

# Methodology

**Company & Signal** - designed so the only variable is retrieval quality:
1. **Retrieval.** Both APIs receive the identical query and return raw search results (Linkup `/search` depth=standard outputType=searchResults; Parallel `/search`).
2. **Synthesis (shared).** Each result set is passed to the same model (Claude Opus 4.8), with an identical prompt and no truncation, instructed to answer using only the provided results. Any answer difference comes purely from what each API retrieved.
3. **Judging (independent).** Each answer is scored blind — the judge never sees which API produced it (Company: Claude Fable 5; Signal: Claude Opus 4.8). Scoring is head-to-head off the same synthesizer, so any judge self-preference applies equally to both sides and cancels. Dimensions: accuracy, completeness, gtm_value, specificity, signal_to_noise. Final score = mean of the five.

**People Search** - each product in its own vendor-recommended people config (no prompt transplant):
1. Linkup `/v1/search` depth=standard + people-targeting prompt; Parallel `/v1beta/search` + people objective + linkedin source filter; both post-filtered to `linkedin.com/in/` profiles.
2. Graded relevance 0–3, judged by an independent model (Claude Fable 5): 3 = exact fit (function + seniority + location), 2 = right person minor mismatch, 1 = real person wrong role, 0 = not a real personal profile.
3. Metrics: Top-Result Hit (rank-1 grade ≥ 2) and Quality Score (mean grade / 3). What makes it distinct from prior people benchmarks: our own GTM-outbound query set, graded relevance instead of binary match, an independent judge from a different model family, and both products tuned to their best config.

**People Research** - same search→synth→judge pipeline as Company & Signal, with a people-tuned synthesis prompt (confirm the right person, don't conflate namesakes) and a 6-dimension judge: accuracy, identity_match, completeness, recency, specificity, gtm_value. Final score = mean of the six.

# Pricing

The Company and Signal benchmarks compare each product at its **standard search tier.**

| API | Tier | Price |
| --- | --- | --- |
| Linkup | Search (standard) | **$5 / 1,000 requests** ($0.005/query) |
| Parallel | Search | **$5 / 1,000 requests** ($0.005/query) |

# Latency

Retrieval latency at the comparable tier (Linkup standard vs Parallel default) — p50, p90, and average over the **full benchmark** (every query, sequential, retrieval call only).

| Benchmark | Linkup p50 | Parallel p50 | Linkup p90 | Parallel p90 | Linkup avg | Parallel avg |
| --- | --- | --- | --- | --- | --- | --- |
| Company Research | **1.58s** | 2.70s | 5.23s | **3.93s** | **2.73s** | 2.84s |
| Signal | **1.79s** | 2.52s | **2.70s** | 4.11s | **1.91s** | 2.72s |
| People Search | **1.97s** | 2.62s | **2.83s** | 3.79s | **2.23s** | 2.82s |
| People Research | **2.60s** | 2.82s | **3.69s** | 4.07s | **2.95s** | 3.08s |

Linkup is faster on the median (p50) and on average across all four benchmarks. Full-coverage run over all 500 queries (Linkup 500/500 successful; Parallel 472/500 after excluding malformed/error responses). Reproduce with `python latency_benchmark.py`; per-query timings in `results/latency_rows.jsonl`.

# Reproduce

```bash
pip install -r requirements.txt
export LINKUP_API_KEY=...      # https://linkup.so
export PARALLEL_API_KEY=...    # https://parallel.ai
export ANTHROPIC_API_KEY=...   # https://console.anthropic.com

python benchmark.py data/company_research_queries.jsonl --out results/company_results.json   # 1. Company Research (250)
python benchmark.py data/signal_bench_100.jsonl --out results/signal_bench_100_opus.json   # 2. Signal (100)
python people_benchmark.py data/people_queries.jsonl                                         # 3. People Search (100) → results/people_results.json
python people_research_benchmark.py data/coresignal_people_queries.jsonl --out results/coresignal_results.json   # 4. People Research (100)

python latency_benchmark.py   # Latency: sequential retrieval-only timing across all 4 benchmarks → results/latency_results.json
```

# Repo structure

```
data/company_research_queries.jsonl   250 company-research queries (id, category, query)
data/signal_bench_100.jsonl        100 signal queries (id, category, query)
data/people_queries.jsonl          100 people-search queries (id, segment, query)
data/coresignal_people_queries.jsonl  100 people-research queries (id, category, query; LinkedIn URL provided)
benchmark.py                       company & signal runner (retrieval → shared synthesis → independent judge)
people_benchmark.py                people runner (best-config retrieval → graded-relevance judge)
people_research_benchmark.py       people-research runner (retrieval → shared synthesis → 7-dim judge)
latency_benchmark.py               latency runner (sequential, retrieval-only timing across all 4 benchmarks)
results/company_results.json       250 company-research scores (id, category, linkup, parallel, totals)
results/signal_bench_100_opus.json 100 signal scores
results/people_results.json        100 people-search scores (graded relevance + top-result hit)
results/coresignal_results.json    100 people-research scores (6 dimensions)
results/latency_results.json       per-benchmark latency stats (p50/p90/p95/p99/mean)
results/latency_rows.jsonl         per-query retrieval latencies (linkup_s, parallel_s)
README.md
```

License: MIT.
