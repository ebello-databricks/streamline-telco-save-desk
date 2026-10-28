# Streamline Telco — Save Desk
### Catch churn while the customer is still talking to us · Telecommunications (consumer postpaid mobile + fibre)

> **FE Bar build.** End-to-end, integrated data journey on the Databricks Data Intelligence Platform.
> **All data is synthetic** (`data/generate_synthetic_data.py`). Streamline Telco is a fictional company.

---

## 1. The outcome (read this first)

**Customer problem.** Streamline Telco loses ~16.8% of its 2M postpaid subscribers a year (~336,000 people,
~€109M revenue). The signals are already there: customers say *"match it or I am porting my number"* on care
calls, network quality degrades, bills jump, commitments end. But they sit in three systems and nobody acts until the
porting request arrives.

**What the build does.** Every night it ingests billing, network, contract and care-call data, uses **AI Functions**
to read every call (sentiment, reason, switching intent), scores every subscriber with an **MLflow churn model**, and
gives the retention team a **Save Desk** app: who to call today, why, what to offer, and one click to log the outcome
(written to **Lakebase**). Managers ask questions in plain English through a **Genie** space.

| KPI (buyer: Chief Customer Officer, Head of Retention) | Today | With Save Desk |
|---|---|---|
| Annual postpaid churn | 16.8% | **15.8%** (−1 pt, year-one target) |
| Subscribers kept / year | — | **20,000** |
| Revenue protected / year | — | **€6.5M** (≈ **€5.0M net** of offers + platform) |
| Precision of the daily call list | random ≈ base rate | **56% in the top 10% = 3.7× lift** |
| Cost per save | — | **≈ €73** |
| Platform cost | — | POC **≈ $1.6k** compute · production **≈ $3.5k / month** (list-price estimate) |

Business figures are illustrative planning assumptions; model figures are measured on the synthetic build.
Full math: `docs/BUSINESS_CASE_AND_COSTS.md`.

**Headline finding (from the run):** subscribers who mention switching on a care call churn at **45.2% vs 10.4%**
(4.3×). `switch_intent`, a Gen AI feature, is the model's #1 driver, and removing the Gen AI call features drops
ROC-AUC from **0.783 → 0.729** (top-10% precision 56% → 42%).

## 2. The integrated journey

```
 synthetic raw data         Databricks Data Intelligence Platform
 subscribers ┐
 contracts   │  Lakeflow        Unity Catalog          AI Functions + MLflow
 usage       ├─► Auto Loader ─► raw/silver/gold ─────► ai_classify / ai_analyze_sentiment / ai_query
 care_calls  │   expectations   tags, column mask,     GradientBoosting churn model (UC registry)
 churn_labels┘                  grants, lineage                   │
                                                                  ▼
                                                        gold.save_list (score, reasons, offer, talk track)
                                                     ┌────────────┴────────────┐
                                          Lakebase synced table          Genie space
                                          + save_actions write-back      (plain-English Q&A)
                                                     │
                                          Databricks App "Save Desk"  ──► outcomes back to the lakehouse → retrain
```

| FE Bar stage | Where |
|---|---|
| Lakeflow: ingest | `notebooks/01_ingest_lakeflow.py` (declarative pipeline, Auto Loader, expectations) |
| Unity Catalog: govern | `notebooks/00_setup_unity_catalog.sql` (medallion, volume, tags, column mask, grants) |
| Gen AI: intelligence | `notebooks/02_genai_enrichment.sql` (AI Functions over every care call) |
| ML: intelligence | `notebooks/03_churn_model.py` (features, MLflow, UC model, save list, ai_query talk track) |
| Lakebase: serving | `notebooks/04_lakebase_serving.py` (synced table + `save_actions` write-back) |
| Genie agent | `genie/genie_space_config.json`, `notebooks/05_genie_agent.py` |
| Databricks App | `app/app.py` (Streamlit, Lakebase-backed) · `app/simulator.html` (workspace simulator for the live demo) · `app/demo.html` (app-only twin) |
| One deployable unit | `databricks.yml` (pipeline, nightly job, Lakebase instance, app) |

## 3. Evidence it ran (text, committed)

- `evidence/model_run_output.txt`: full log of all 8 stages (silver → Gen AI → features → model → save list → serving → Genie → app data)
- `evidence/model_metrics.json`: ROC-AUC 0.783, PR-AUC 0.486, top-decile precision 0.562 / lift 3.73×, Gen AI ablation, feature importances
- `evidence/query_results.md`: 5 Genie business questions with SQL and answers
- `data/output/*_sample.csv`: raw and gold samples (`gold_save_list_sample.csv` = the agent's list)
- `app/demo_data.js`: the top 300 rows the app shows

`data/run_local_pipeline.py` runs the same feature, model and offer code the workspace notebooks import
(`03_churn_model.py` loads it directly), so local evidence and workspace logic are identical. Locally, the LLM is
replaced by a deterministic lexicon and Lakebase by SQLite, both labelled as such in the log.

Reproduce (~15 s):
```bash
uv venv --python 3.12 .venv && . .venv/bin/activate && uv pip install numpy pandas scikit-learn pyarrow
python data/generate_synthetic_data.py && python data/run_local_pipeline.py
python data/export_simulator_data.py
open app/simulator.html     # Databricks workspace simulator with the Save Desk app
```

## 4. Decisions, AI usage, demo
- `docs/DECISIONS.md`: trade-offs (AI Functions vs fine-tune, GBM vs deep learning, Lakebase vs Delta reads, batch vs real time, rule-based offers first)
- `docs/AI_USAGE.md`: how Claude Code was used, and what I decided
- `docs/ROLEPLAY.md`: audience, tell-show-tell script, objection handling
- `deck/Streamline-Telco-Save-Desk.pdf`: business deck (15 slides)
