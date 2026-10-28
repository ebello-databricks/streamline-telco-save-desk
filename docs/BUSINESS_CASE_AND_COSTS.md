# Business case and costs

Streamline Telco is fictional. Business inputs are **planning assumptions**, replaced by Streamline actuals in POC week 1.
Model inputs come from `evidence/model_metrics.json`.

## Value

| Input | Value | Source |
|---|---|---|
| Postpaid subscribers | 2,000,000 | assumption |
| Monthly churn | 1.4% (16.8% / year) | assumption |
| Subscribers lost / year | 336,000 | 2M × 16.8% |
| ARPU | €27 / month (€324 / year) | assumption |
| Revenue lost to churn / year | €108.9M | 336k × €324 |
| Precision of top-10% list | 56.2% | build (model_metrics.json) |
| Save rate on reached churners | 25% | assumption |
| Average offer cost | €40 | offer mix of High+Critical in build: (704×€60 + 683×€15 + 434×€45 + 4×€10) / 1,825 = €39.5 |

| Year-one result | Value |
|---|---|
| Target | −1.0 pt annual churn → **20,000 saves** |
| Churners to reach | 20,000 / 25% = 80,000 (24% of all churners; model recall in top decile is 37%) |
| Contacts | 80,000 / 0.562 ≈ 143,000 / year ≈ 550 per working day |
| Revenue protected | 20,000 × €324 = **€6.48M** |
| Offer cost | (20,000 saves + 25% × 62,600 contacted non-churners) × €40 ≈ **€1.43M** |
| Platform | ≈ $42k ≈ €0.04M |
| **Net benefit** | **≈ €5.0M / year** |
| Cost per save | ≈ €73 |
| Downside (save rate halves to 12.5%, same contacts) | 10,000 saves → €3.24M − €1.03M − €0.04M ≈ **€2.2M net** |

## Cost (Databricks list-price estimates, AWS, pay-as-you-go)

Unit prices: Foundation Model API Llama 3.3 70B **$0.50 / 1M input, $1.50 / 1M output tokens**
(7.143 / 21.429 DBU per 1M tokens; https://www.databricks.com/product/pricing/foundation-model-serving, read directly).
The following were **not read directly on the pricing pages** (JS-rendered) and must be validated in Lakemeter:
serverless jobs and pipelines $0.40/DBU; serverless SQL $0.70/DBU (Small = 12 DBU/h); Lakebase $0.50/DBU, assuming
1 CU ≈ 1 DBU/h; Databricks App 0.5 DBU/h at $0.70/DBU.

Volume drivers: synthetic data has 0.344 care calls per subscriber per month → ~690k calls / month at 2M subscribers.
~1,100 tokens per AI function call (≈1,000-token transcript + prompt), 3 functions → 3,300 input tokens per call.

| Component | POC (6 weeks, 200k subscribers) | $ | Production (per month) | $ |
|---|---|---|---|---|
| Gen AI on calls | 200k calls × 3.3k tokens, plus re-runs | 400 | 690k × 3.3k = 2.28B in + 21M out | 1,170 |
| Lakeflow pipeline | 150 DBU | 60 | 600 DBU | 240 |
| ML train + score | 200 DBU | 80 | 300 DBU | 120 |
| SQL warehouse (Genie, SQL tasks) | Small, 3 h × 30 days = 1,080 DBU | 760 | Small, (4 h × 22) + (1 h × 30) = 1,416 DBU | 990 |
| Lakebase | 1 CU × 300 h | 150 | 2 CU × 730 h | 730 |
| Databricks App | 300 h × 0.5 DBU | 105 | 730 h × 0.5 DBU | 255 |
| Cloud storage | < 100 GB | 5 | ~1 TB | 25 |
| **Total** | | **≈ 1,560** | | **≈ 3,530 (≈ $42k / year)** |

Optimisation: one `ai_query` returning JSON (sentiment + intent + switch intent) instead of three functions cuts
tokens to ~1,200 per call → Gen AI ≈ $476 / month → production ≈ **$2.8k / month**.

People (not priced): Streamline sponsor, a retention lead and one data engineer; Databricks account team support.
