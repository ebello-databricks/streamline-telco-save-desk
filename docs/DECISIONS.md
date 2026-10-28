# Decisions and trade-offs

Also the answer sheet for the technical persona in the role-play.

### 1. AI Functions in SQL, not a fine-tuned or self-hosted model
- **Chose:** `ai_analyze_sentiment`, `ai_classify`, `ai_query` on Databricks-hosted models, run incrementally on new calls only.
- **Why:** short transcripts, generic task. No model to host, transcripts stay inside the governed platform, ships in days.
- **Trade-off:** per-token cost at scale (≈$1.2k/month at 690k calls). Mitigation: one combined JSON prompt (about −60% tokens). Fine-tune only if a Streamline-specific taxonomy requires it.
- **Proof of value:** ablation in `evidence/model_metrics.json`: without the Gen AI call features, ROC-AUC falls from 0.783 to 0.729 and top-decile precision from 0.562 to 0.422.

### 2. Gradient boosting, not deep learning
- **Why:** tabular data with 21 features. Agents need the "why" (top 3 reasons on every row). Trains in seconds and retrains weekly.
- **Trade-off:** a more complex model might gain some AUC but lose explainability; not worth it for a save desk.

### 3. Lakebase for the app, not direct Delta reads
- **Why:** the app does point lookups and transactional write-back (`save_actions`), which is OLTP work. A synced table keeps it declarative.
- **Trade-off:** a second store. Accepted because sync is managed and outcomes in Postgres can be read by any CRM.

### 4. Rule-based next-best-offer first, uplift model later
- **Why:** the retention lead owns the offer catalogue; rules mapped to the primary driver (network → fix + credit, price → loyalty match, contract → early renewal) are auditable from day 1.
- **Trade-off:** not optimised yet. Outcomes logged in the app become the training data for an uplift model in phase 3.

### 5. Nightly batch scoring, not real time
- **Why:** save decisions are made daily; batch cuts cost and complexity.
- **Trade-off:** a call made at 10:00 affects the score the next morning. Real-time scoring on call end is a phase-3 option (Model Serving + Lakebase).

### 6. Synthetic data with learnable signal
- **Why:** customer-safe by construction and reproducible (seed 42). Churn is generated from realistic drivers so the model learns real patterns.
- **Trade-off:** the synthetic 60-day churn base rate (15.1%) is higher than a real monthly rate; it is used only for the lift math. The business case uses 1.4% monthly churn as a separate, explicit assumption.

### 7. Local mirror for evidence
- **Why:** the evaluator reads text. `data/run_local_pipeline.py` runs the same feature, model and offer code the workspace notebook imports, and commits the output. The LLM is replaced by a lexicon and Lakebase by SQLite, both labelled.
- **Trade-off:** local Gen AI is a stand-in; in the workspace the AI Functions do this step.
