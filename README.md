# Linkup vs Parallel - GTM Benchmark

A reproducible benchmark comparing **Linkup Search** and **Parallel Search** on go-to-market (GTM) company-research queries - the enrichment and prospecting questions sales/growth teams run at scale. Both APIs are tested at their comparable search tier and the same price point. Results are judged by an independent LLM on six GTM-relevant quality dimensions.

## Results

250 GTM company-research queries. Linkup Search vs Parallel Search, scored 0–10 per dimension.

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

## Pricing

Both products are priced per request, and the tiers compared here cost the **same**:

| API | Tier | Price |
| --- | --- | --- |
| Linkup | Search (standard) | **$5 / 1,000 requests** ($0.005/query) |
| Parallel | Search | **$5 / 1,000 requests** ($0.005/query) |

Like-for-like at an identical price point - the quality difference does not come at a higher cost.

## Methodology

Designed so the **only variable is retrieval quality**.

1. **Retrieval.** Both APIs receive the identical query and return raw search results (Linkup `/search` depth=standard outputType=searchResults; Parallel `/search`).
2. **Synthesis (shared).** Each result set is passed to the **same model (Claude Opus 4.8)**, identical prompt, no truncation, instructed to answer using only the provided results. Any answer difference comes purely from what each API retrieved.
3. **Judging (independent).** Each answer scored blind by a **different model (Claude Fable 5)** — different family from the synthesizer, to avoid self-preference. Judge never sees which API produced an answer.

**Dimensions:** accuracy, completeness, gtm_value, specificity, source_quality, signal_to_noise. Final score = mean of the six.

## Query selection

The 250 queries were randomly sampled from real Linkup production traffic - anonymized GTM company-research queries run by customers at scale. We filtered production logs to company-research intent (profile, enrichment, identification, financial lookup, website analysis), then drew a sample. 

## Example queries

- **Company enrichment:** List every company logo in "trusted by"/"our customers" sections on {company_url}.
- **Company profile:** What is the business activity of {company} (start from {company_url})? Focus on value-chain position, products/services, end-markets.
- **Company identification:** What company operates {domain}? Common name, main product, recent news, notable customers, funding.
- **Financial lookup:** {company} annual revenue / EBITDA — official sources.
- **Website analysis:** Visit {company_url}; determine if the product is PLG (self-serve signup, free trial, public pricing, product access without sales).

## Reproduce

```
pip install anthropic httpx rich
export LINKUP_API_KEY=... PARALLEL_API_KEY=... ANTHROPIC_API_KEY=...
python benchmark.py data/queries.jsonl
```

## Repo structure

- `data/queries.jsonl` — 250 GTM queries (id, category, query)
- `benchmark.py` — runner (retrieval → shared synthesis → independent judge)
- `results/results.json` — per-query, per-dimension scores
- `README.md`

License: MIT.
