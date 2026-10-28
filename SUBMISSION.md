# FE Bar — submission pack (copy-paste into the form)

## Form fields

**Customer name**
```
Streamline Telco (fictional; synthetic data)
```

**Industry / vertical**
```
Telecommunications — consumer postpaid mobile and fibre broadband (Communications, Media & Entertainment)
```

**What is the business challenge you are solving?**
```
Streamline Telco loses about 16.8% of its 2 million postpaid subscribers a year (~336,000 customers, ~€109M of revenue). The retention team only acts when a customer requests a porting code, when the decision is already made. The early signals exist but sit in three disconnected places: what customers say on care calls ("match it or I am porting my number"), network experience (dropped calls, slow data) and billing/contract events (bill shock, commitment ending). Nobody reads the calls at scale, offers are generic, and analysts wait days for BI tickets to answer "who, where and why". The Chief Customer Officer needs churn down and revenue kept; the Head of Retention needs a daily list of who to call, why, and what to offer, at a controlled cost per save.
```

**How does your Databricks solution address this challenge?**
```
"Save Desk": one integrated, governed journey on the Databricks Data Intelligence Platform, deployed as one Asset Bundle (databricks.yml).
1) Lakeflow: a Lakeflow Declarative Pipeline with Auto Loader ingests the raw synthetic landing files (subscribers, contracts, monthly usage and network experience, care-call transcripts, churn labels) from a UC Volume into bronze, then applies expectations into silver (notebooks/01_ingest_lakeflow.py).
2) Unity Catalog: one catalog with raw/silver/gold schemas, a landing Volume, a "sensitive" tag and a column mask on transcripts (only the data team sees raw text), gold-only grants for retention, and automatic lineage (00_setup_unity_catalog.sql).
3) Gen AI: AI Functions (ai_analyze_sentiment, ai_classify, ai_query on Llama 3.3 70B) read every care call incrementally for sentiment, intent and switching intent (02_genai_enrichment.sql).
4) ML: a gold feature table (network + billing + contract + Gen AI call features) trains a GradientBoosting churn model tracked in MLflow and registered in Unity Catalog. Every subscriber is scored into gold.save_list with a risk band, value at risk, top 3 reasons, a next best offer by driver (network fix / loyalty price match / early renewal) and an ai_query talk track for the agent (03_churn_model.py).
5) Lakebase: gold.save_list is synced to Lakebase Postgres for millisecond lookups, and a save_actions table receives agent outcomes (transactional write-back), which flow back to retrain the model (04_lakebase_serving.py).
6) Genie agent: a Genie space over the gold tables with instructions, sample questions and trusted SQL, so managers ask in plain English, e.g. "Which region has the most at-risk subscribers because of network problems?" (genie/genie_space_config.json, 05_genie_agent.py).
7) Databricks App: the Save Desk (app/app.py, Streamlit on Lakebase), with KPIs, a ranked save list, a subscriber card with reasons, offer and talk track, and one-click outcome logging. app/demo.html is its click-through twin on the real gold output, used for the live demo.
Execution evidence is committed as text: evidence/model_run_output.txt (all 8 stages), evidence/model_metrics.json, evidence/query_results.md (Genie questions with SQL and answers), data/output/*_sample.csv. data/run_local_pipeline.py runs the same feature/model/offer code that the workspace notebook imports; the LLM and Lakebase have local stand-ins (lexicon, SQLite), labelled in the log.
```

**What AI tools did you use, and what was your workflow? What decisions and trade-offs did you have to make for your build?**
```
Tool: Claude Code (CLI) as a pair-programmer, plus a sub-agent to look up public Databricks list prices. Workflow: I framed the customer, buyer (CCO), domain owner (Head of Retention), KPIs and the thesis that the care call already contains the churn signal. AI drafted the synthetic generator to my driver design, then the pipeline, notebooks, app, deck and docs; I reviewed every stage. Iterations I drove: (a) on the first app render the driver label contradicted the reasons shown to the agent, so I changed the driver logic to follow hard signals and added missing reasons; (b) I asked for an ablation to measure the value of Gen AI instead of claiming it; (c) only the Foundation Model API price could be verified on the pricing page, so I labelled every other rate as an estimate to validate in Lakemeter.
Trade-offs (docs/DECISIONS.md): AI Functions in SQL instead of a fine-tune (fast and governed; per-token cost, mitigated by incremental processing and a combined prompt, about −60% tokens); gradient boosting instead of deep learning (agents need the "why"; retrains in minutes); Lakebase instead of Delta reads for the app (OLTP lookups and write-back; a second store, kept in sync declaratively); rule-based offers first, uplift model later on logged outcomes; nightly batch instead of real time (save decisions are daily); synthetic data with learnable drivers (customer-safe and reproducible; the 15.1% synthetic 60-day base rate is used only for lift, while the business case uses a separate 1.4% monthly churn assumption).
```

**What are the business outcomes and impact?**
```
Measured on the build (synthetic, 20,000 subscribers, 13,749 calls, 25% hold-out): ROC-AUC 0.783; the top-10% call list has 56% precision, 3.7× the 15.1% base rate. Customers who mention switching on a care call churn at 45.2% vs 10.4% (4.3×). Gen AI call features add +0.053 AUC (0.729 → 0.783) and lift top-10% precision from 42% to 56%; switching intent is the #1 feature.
Business case (planning assumptions for Streamline: 2M postpaid subscribers, 1.4% monthly churn, €27 ARPU, 25% save rate, €40 average offer): a 1-point annual churn reduction (16.8% → 15.8%) = 20,000 subscribers kept per year = €6.48M revenue protected; minus €1.42M offers and ~€0.04M platform ≈ €5.0M net per year; ≈ €73 per save; ~550 targeted calls per working day. Downside at half the save rate: ≈ €2.2M net.
Cost (Databricks list-price estimates, AWS): POC ≈ $1.6k compute over 6 weeks (200k-subscriber sample); production ≈ $3.5k/month (≈ $42k/year), ≈ $2.8k/month with one combined AI prompt.
Plan: 6-week POC (gates: ≥ 2.5× lift on real history, ≥ 85% agreement of AI switch intent with 500 calls labelled by people) → 2-month pilot with a randomised control group (go if save rate is ≥ 5 points above control at ≤ €80 per save) → scale with weekly retraining on outcomes.
```

**GitHub repo link** — see "Steps you do" below.

**Presentation deck** — attach `deck/Streamline-Telco-Save-Desk.pdf` (15 slides + closing, official Databricks template, text-selectable).

**Local repo folder** — choose a **fresh clone** of the GitHub repo (step 3 below), not this Drive folder: it also contains `.venv/` and your FE Bar notes file `requirements.txt`, which the uploader would read as code.

**Conversation ID (optional)** — this Claude Code session ID (run `/status` in Claude Code, or see the form's help link).

**"AI Customer Challenge build" checkbox** — leave **unchecked** (this is an original build, not the Customer Challenge repo).

**Attestation** — tick, and sign with your full name.

## Steps you do (in order)
1. Create a new GitHub repo under your account, e.g. `streamline-telco-save-desk` (public, or connect GitHub on the form if it is in the EMU org).
2. `git remote set-url origin https://github.com/<you>/streamline-telco-save-desk.git && git push -u origin main`
3. Open the repo in a private browser window to confirm it is readable, then `git clone <repo-url> ~/Documents/streamline-telco-save-desk`: that clean clone is the local folder you select on the form.
4. Fill in the form with the blocks above, attach the PDF, choose the local folder, sign, submit.
5. Role-play tab: follow `docs/ROLEPLAY.md`, with `app/demo.html` open in a browser tab.

## Element checklist
| FE Bar element | Where | Evidence |
|---|---|---|
| Lakeflow | `notebooks/01_ingest_lakeflow.py`, `databricks.yml` pipeline | run log `[1 silver]` |
| Unity Catalog | `notebooks/00_setup_unity_catalog.sql` | schemas/mask/grants in code |
| Lakebase | `notebooks/04_lakebase_serving.py`, `databricks.yml` instance + app resource | run log `[6 serve]` |
| ML + Gen AI | `notebooks/02_genai_enrichment.sql`, `notebooks/03_churn_model.py` | `model_metrics.json`, run log `[2]` to `[5]` |
| Genie agent | `genie/genie_space_config.json`, `notebooks/05_genie_agent.py` | `evidence/query_results.md` |
| Databricks App | `app/app.py`, `app/app.yaml`, `app/demo.html` | `app/demo_data.js` |
| Synthetic raw data | `data/generate_synthetic_data.py` | `data/output/generation.log`, `*_sample.csv` |
