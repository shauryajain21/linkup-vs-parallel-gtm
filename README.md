# Linkup Search vs Parallel Search — GTM Retrieval Benchmarks

A suite of reproducible benchmarks comparing **Linkup Search** and **Parallel Search** across the GTM retrieval surface — the company-research, buying-signal, and people-search questions sales and growth teams run at scale. Every benchmark is designed so the **only variable is retrieval quality**: the same query goes to both APIs, the same downstream model turns each result set into an answer, and an independent model judges the answers blind.

Every benchmark compares the two products' **search APIs** (Linkup `/search`, Parallel `/search`) head-to-head.

## Benchmarks in this repo

| # | Benchmark | What it tests | Queries | Headline |
| --- | --- | --- | --- | --- |
| 1 | **Company Research** | Enrichment & prospecting on a company | 250 | Linkup **7.2** vs Parallel 6.0 — wins all 6 dimensions |
| 2 | **Signal** | Real-time GTM buying signals | 50 | Linkup **6.9** vs Parallel 6.7 — leads/ties every dimension |
| 3 | **People Search** | Right person's LinkedIn by role/seniority/location | 100 | Linkup **76%** vs Parallel 48% top-result hit |

Details, methodology, and reproduce steps for each are below.

---

# 1. Company Research Benchmark

250 GTM company-research queries — the enrichment and prospecting questions sales/growth teams run at scale. Both APIs are tested at their comparable search tier and the same price point, and the answers are judged by an independent LLM (Claude Fable 5) on six GTM-relevant quality dimensions, scored 0–10.

## Results — 250 queries

| Dimension | Linkup | Parallel |
| --- | --- | --- |
| Accuracy | **8.3** | 7.1 |
| Completeness | **6.1** | 4.8 |
| GTM Value | **6.8** | 5.5 |
| Specificity | **7.8** | 6.8 |
| Source Quality | **6.5** | 5.6 |
| Signal-to-Noise | **7.5** | 6.2 |
| **Overall** | **7.2** | **6.0** |

**Linkup outperforms Parallel on all six dimensions**, winning **191 / 250** queries head-to-head.

### By query category

| Category | Linkup | Parallel | n |
| --- | --- | --- | --- |
| Company profile | **7.5** | 5.9 | 76 |
| Company enrichment | **7.4** | 5.2 | 63 |
| Company identification | **6.7** | 6.2 | 49 |
| Financial lookup | **6.7** | 6.5 | 36 |
| Website analysis | **7.5** | 6.9 | 25 |

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

A separate run on **real-time GTM "buying signal" queries** — breach disclosures, executive appointments, funding rounds, layoffs, M&A, compliance actions, IPO filings, and geographic expansion. These are the event-detection questions sales and security teams run for outbound timing: the trigger that says *reach out to this account now.* It uses the same pipeline as the company benchmark (identical query → shared Opus 4.8 synthesis → blind Fable 5 judge).

## Results — 50 queries

| Dimension | Linkup | Parallel |
| --- | --- | --- |
| Accuracy | **7.2** | 7.1 |
| Completeness | **5.5** | 5.3 |
| GTM Value | **6.7** | 6.5 |
| Specificity | 8.1 | 8.1 |
| Source Quality | 6.2 | 6.2 |
| Signal-to-Noise | **7.4** | 7.2 |
| **Overall** | **6.9** | **6.7** |

Linkup leads or ties on every dimension. The two are closely matched on this workload overall, with Linkup's clearest edge on the largest categories.

### By signal category

| Category | Linkup | Parallel | n |
| --- | --- | --- | --- |
| Security / breach | **6.9** | 6.5 | 16 |
| Leadership change | **8.0** | 7.0 | 7 |
| Funding | 7.2 | **7.3** | 7 |
| Layoff | 6.8 | **7.2** | 5 |
| M&A | 7.0 | **7.3** | 5 |
| Compliance | 6.0 | **6.7** | 5 |
| IPO | **5.2** | 5.1 | 3 |
| Expansion | **6.1** | 5.9 | 2 |

Linkup's strongest edge is on **security-breach** and **leadership-change** detection — the two largest categories. Parallel edges ahead on funding, layoff, M&A, and compliance signals, mostly by thin margins.

### Query selection

The 50 signal queries are a hand-built set of GTM buying-signal questions, phrased the way a sales or security vendor would actually run them for outreach timing — naming a specific company and domain, the facts to confirm (numbers, dates, root cause), and the sales context.

### Example queries

- **Leadership:** Which companies announced a new CISO, CIO, or VP of Security in the last 60 days? List each company, the executive, their prior employer, and the announcement date with a source URL.
- **Funding:** Has any company raised a mega-round (over $100M) in the last 30 days? List the company, amount, round stage, lead investor, and date with sources.
- **M&A:** Which mergers or acquisitions over $1B were announced in 2026? For each, list the acquirer, target, deal value, and announcement date with a source URL.
- **Security:** Did Coupang (coupang.com) disclose a data breach exposing customer accounts? Confirm whether a breach occurred, how many accounts were affected, the root cause, the exposure and disclosure dates, and the data categories involved — with source URLs.

---

# 3. People-Search Benchmark

100 GTM people-search / prospecting queries — finding the right person's LinkedIn profile by role, seniority, and location.

## Results — 100 queries

| Metric | Linkup | Parallel |
| --- | --- | --- |
| **Top-Result Hit** | **76%** | 48% |
| Quality Score | 55% | 59% |

- **Top-Result Hit** — is the #1 returned result the right person (graded relevance ≥ 2)? **Linkup's first result is right 76% of the time vs Parallel's 48%** — Linkup puts the correct prospect at the top far more often.
- **Quality Score** — mean graded relevance across the top-10 (0–3 normalized). Roughly even (Parallel a touch higher on breadth).

### Top-Result Hit by GTM persona

| Segment | Linkup | Parallel |
| --- | --- | --- |
| Engineering | 85% | 50% |
| Marketing | 80% | 45% |
| Product | 80% | 60% |
| Ops / People | 70% | 35% |
| Revenue | 65% | 50% |

Linkup leads Top-Result Hit across **every** persona segment.

### What this measures

- **Top-Result Hit** rewards precision — putting the right person first. This is where Linkup wins.
- **Quality Score** rewards breadth/relevance across the whole list — roughly a tie.

Read together: **Linkup is more precise at the top of the list; Parallel returns a comparably relevant list overall.** If "right person, first result" is what matters for outreach, Linkup leads.

### Example queries

- **Product:** product manager at AI startups in London
- **Revenue:** head of partnerships at B2B SaaS companies in Bangalore
- **Marketing:** director of demand generation at cybersecurity companies in San Francisco
- **Ops / People:** head of people in Singapore, 5+ years
- **Engineering:** staff engineer at developer-tools companies in Berlin

---

# Methodology

**Company & Signal** - designed so the only variable is retrieval quality:
1. **Retrieval.** Both APIs receive the identical query and return raw search results (Linkup `/search` depth=standard outputType=searchResults; Parallel `/search`).
2. **Synthesis (shared).** Each result set is passed to the same model (Claude Opus 4.8), with an identical prompt and no truncation, instructed to answer using only the provided results. Any answer difference comes purely from what each API retrieved.
3. **Judging (independent).** Each answer is scored blind by a different model (Claude Fable 5) — a different family from the synthesizer, to avoid self-preference. The judge never sees which API produced an answer. Dimensions: accuracy, completeness, gtm_value, specificity, source_quality, signal_to_noise. Final score = mean of the six.

**People Search** - both products in best people config (symmetric, neither vanilla):
1. Linkup `/v1/search` depth=deep + people-targeting prompt; Parallel `/v1beta/search` + people objective + linkedin source filter; both post-filtered to `linkedin.com/in/` profiles.
2. Graded relevance 0–3, judged by an independent model (Claude Fable 5): 3 = exact fit (function + seniority + location), 2 = right person minor mismatch, 1 = real person wrong role, 0 = not a real personal profile.
3. Metrics: Top-Result Hit (rank-1 grade ≥ 2) and Quality Score (mean grade / 3). What makes it distinct from prior people benchmarks: our own GTM-outbound query set, graded relevance instead of binary match, an independent judge from a different model family, and both products tuned to their best config.

# Pricing

The Company and Signal benchmarks compare each product at its **standard search tier.**

| API | Tier | Price |
| --- | --- | --- |
| Linkup | Search (standard) | **$5 / 1,000 requests** ($0.005/query) |
| Parallel | Search | **$5 / 1,000 requests** ($0.005/query) |

# Reproduce

```bash
pip install -r requirements.txt
export LINKUP_API_KEY=...      # https://linkup.so
export PARALLEL_API_KEY=...    # https://parallel.ai
export ANTHROPIC_API_KEY=...   # https://console.anthropic.com

python benchmark.py data/company_research_queries.jsonl --out results/company_results.json   # 1. Company Research (250)
python benchmark.py data/news_signal_queries.jsonl --out results/news_signal_results.json   # 2. Signal (50)
python people_benchmark.py data/people_queries.jsonl                                         # 3. People Search (100) → results/people_results.json
```

# Repo structure

```
data/company_research_queries.jsonl   250 company-research queries (id, category, query)
data/news_signal_queries.jsonl     50 signal queries (id, category, query)
data/people_queries.jsonl          100 people-search queries (id, segment, query)
benchmark.py                       company & signal runner (retrieval → shared synthesis → independent judge)
people_benchmark.py                people runner (best-config retrieval → graded-relevance judge)
results/company_results.json       250 company-research scores (id, category, linkup, parallel, totals)
results/news_signal_results.json   50 signal scores
results/people_results.json        100 people-search scores (graded relevance + top-result hit)
README.md
```

License: MIT.
