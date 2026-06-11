# Linkup vs Parallel — GTM Benchmark

A reproducible benchmark comparing **Linkup Search** and **Parallel Search** on
go-to-market (GTM) company-research queries — the kind of enrichment and prospecting
questions sales and growth teams run at scale.

Both APIs are tested at their comparable search tier and the same price point. Results
are judged by an independent LLM on six GTM-relevant quality dimensions.

---

## Results

250 GTM company-research queries. Linkup Search vs Parallel Search, each scored 0–10 per dimension.

| Dimension | Linkup | Parallel |
|---|---:|---:|
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
|---|---:|---:|---:|
| Company profile | **7.5** | 5.9 | 76 |
| Company enrichment | **7.4** | 5.2 | 63 |
| Company identification | **6.7** | 6.2 | 49 |
| Financial lookup | **6.7** | 6.5 | 36 |
| Website analysis | **7.5** | 6.9 | 25 |

---

## Pricing

Both products are priced per request, and the tiers compared here cost the **same**:

| API | Tier | Price |
|---|---|---|
| Linkup | Search (standard) | **$5 / 1,000 requests** ($0.005/query) |
| Parallel | Search | **$5 / 1,000 requests** ($0.005/query) |

This is a like-for-like comparison at an identical price point — the quality difference
above does not come at a higher cost.

---

## Methodology

The benchmark is designed so the **only variable is retrieval quality**.

1. **Retrieval.** Both APIs receive the identical query and return raw search results:
   - Linkup: `POST /v1/search` with `depth=standard`, `outputType=searchResults`
   - Parallel: `POST /v1beta/search` with `max_results=10`
2. **Synthesis (shared).** Each API's result set is passed to the **same model
   (Claude Opus 4.8)** with an identical prompt and no truncation, instructed to answer
   *using only the provided search results*. Because the synthesizer is shared, any
   difference in the answer comes purely from what each API retrieved.
3. **Judging (independent).** Each answer is scored blind by a **different model
   (Claude Fable 5)** — different model family from the synthesizer, to avoid self-preference.
   The judge never sees which API produced an answer, nor the competing answer.

### Why this is fair
- Same queries for both APIs.
- Same price tier (see Pricing).
- Shared synthesizer isolates retrieval quality; neither API's own LLM is involved.
- Independent judge (different model family) scores blind.
- No truncation — each API's full output is used.

### Dimensions
| Dimension | Question the judge answers |
|---|---|
| Accuracy | Factually grounded and about the right company? |
| Completeness | Fully addresses everything the question asked? |
| GTM Value | Actionable for a sales / GTM professional? |
| Specificity | Concrete details (numbers, names, products) vs vague generalities? |
| Source Quality | Authoritative, on-target sources vs random pages? |
| Signal-to-Noise | Dense with relevant info vs padded with boilerplate? |

Final score per answer = mean of the six dimensions.

---

## Query selection

<!-- TODO (team): describe how the query set was assembled before publishing.
     Do not finalize this section without sign-off. -->
*(Section to be completed.)*

---

## Example queries

The benchmark covers real GTM research tasks. A few representative examples:

**Company enrichment**
> List every company logo visible in "trusted by", "our customers", or "used by" sections on `{company_url}`. Only include companies shown on the homepage, customer page, or testimonial sections.

**Company profile**
> What is the business activity of `{company}` (use `{company_url}` as your starting point)? Focus on the positioning on the value chain, the products & services, and the end-markets served.

**Company identification**
> What company operates the website at `{domain}`? What is the company's common name, main product, recent news, notable customers, competitive position, and funding?

**Financial lookup**
> `{company}` annual revenue / EBITDA — official sources.

**Website analysis**
> Visit `{company_url}`. Based on the homepage, pricing, product, and about pages, determine whether the product is Product-Led Growth (PLG): self-serve signup, free trial/freemium, public pricing, and product access without sales.

The full 250-query set is in [`data/queries.jsonl`](data/queries.jsonl).

---

## Reproduce it

```bash
git clone https://github.com/shauryajain21/linkup-vs-parallel-gtm
cd linkup-vs-parallel-gtm
pip install anthropic httpx rich

export LINKUP_API_KEY=...      # https://linkup.so
export PARALLEL_API_KEY=...    # https://parallel.ai
export ANTHROPIC_API_KEY=...   # https://console.anthropic.com

python benchmark.py data/queries.jsonl
```

The script prints the results table and writes per-query scores to `results/results.json`.

---

## Repo structure

```
data/queries.jsonl     250 GTM company-research queries (id, category, query)
benchmark.py           the benchmark runner (retrieval → shared synthesis → independent judge)
results/results.json   per-query, per-dimension scores for both APIs
README.md              this file
```

## License

MIT.
