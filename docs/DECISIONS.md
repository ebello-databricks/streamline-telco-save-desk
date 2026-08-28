# Decisions & trade-offs

The FE Bar rewards documented reasoning. These are the calls I made and why —
also the objection-handling script for the roleplay's technical persona.

### 1. GradientBoosting, not a deep model
- **Chose:** `GradientBoostingClassifier` (sklearn, MLflow-tracked).
- **Why:** tabular data at 15k rows; the retention team must **trust the "why"**,
  so per-customer feature attributions matter more than a fraction of a point of
  AUC. Trains in seconds, cheap to retrain nightly.
- **Trade-off:** a deep/tabular-transformer model *might* squeeze more AUC, at the
  cost of explainability, cost, and ops burden — not worth it here. Result stands
  on its own: **ROC-AUC 0.765, 3.04× top-decile lift.**

### 2. Foundation Model API (`ai_query`), not a fine-tuned model
- **Chose:** built-in `ai_analyze_sentiment` / `ai_classify` / `ai_query` in SQL.
- **Why:** transcripts are short and the task (sentiment, intent, switch-intent)
  is well within a general LLM. Zero hosting, nothing leaves UC, and it ships in a
  day instead of a fine-tune cycle.
- **Trade-off:** per-call inference cost at full scale; mitigated by scoring only
  new calls incrementally and caching. A fine-tune becomes worth it only if volume
  or a domain-specific taxonomy demands it.

### 3. Lakebase for serving, not query-from-Delta
- **Chose:** sync `gold.churn_scores` into Lakebase (Postgres) for the app.
- **Why:** the cockpit does **point lookups + action write-back** — an OLTP
  pattern. Delta is built for analytical scans, not per-row app latency.
- **Trade-off:** a second store to keep in sync; handled by a managed synced table
  so it's declarative, not a hand-rolled reverse-ETL job.

### 4. Synthetic data, not scrubbed real data
- **Chose:** generate the dataset (`generate_synthetic_data.py`) with churn made
  genuinely learnable from voice + billing signals.
- **Why:** **customer-safe by construction** (mandatory for the FE Bar), fully
  reproducible (seeded), and it lets me prove the thesis — voice features end up as
  the top predictors — without touching a single real record.
- **Trade-off:** synthetic churn base rate (22.3%) is higher and cleaner than the
  real market (~12%). I keep those two numbers explicitly distinct: 22.3% is the
  model's base rate for the lift math; 12%→11% is the business case on real market
  churn.

### 5. Voice as a first-class feature, not a side dashboard
- **Chose:** fold sentiment/intent/switch-intent into the churn feature table.
- **Why:** the entire point is that the call centre already knows who's leaving.
  Proven: `churn_mentions` is the #1 feature (importance 0.30).
- **Trade-off:** depends on call coverage — customers who never call have weaker
  signal, so billing/contract features carry them (and they're lower-risk anyway).
