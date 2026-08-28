# FE Bar — Submission checklist

**Build:** Plenitude "Voice-to-Retention" · **Industry:** Retail energy (B2C, Italy)
· **Problem:** contact-centre voice signal is lost, so churn is only caught after
customers leave.

## Required elements — the integrated journey

| FE Bar element | Where it lives | Status |
|---|---|---|
| **Lakeflow** — ingest raw data | `notebooks/01_ingest_lakeflow.py` (Auto Loader → bronze → silver, DLT expectations) | ✅ |
| **Unity Catalog** — govern it | `notebooks/00_setup_unity_catalog.sql` (medallion, volume, tags, grants) | ✅ |
| **Lakebase** — operational serving | `notebooks/04_lakebase_serving.py` (synced Postgres + `retention_actions` write-back) | ✅ |
| **ML or Gen AI** — make it intelligent | `notebooks/02_genai_enrichment.py` (FM API) **+** `notebooks/03_churn_model.py` (GBM, MLflow) | ✅ both |
| **Genie Room** — NL queryable | `notebooks/05_genie_room.py` + `genie/genie_space_config.json` | ✅ |
| **A Databricks App** — surface to business | `app/app.py` (+ `app.yaml`, `requirements.txt`) | ✅ |
| Raw data (synthetic/public) | `data/generate_synthetic_data.py` → `data/output/` | ✅ synthetic |
| One deployable unit | `databricks.yml` (Asset Bundle) | ✅ |

## What to include in the submission

- **(1) The build (required)** — code + notebooks + app + dashboard, **with run
  evidence readable as text**: `evidence/model_metrics.json`,
  `evidence/model_run_output.txt`, `evidence/query_results.md`, and committed
  `data/output/*.parquet` + `*_sample.csv`. Source alone would not pass the Build
  domain; the committed execution output does.
  → **Push this folder to a GitHub repo and put the repo link in the form.** Make
  it public, or connect GitHub from the submission form if it lives in a private
  EMU org. (Verify the validator can read it *before* submitting.)
- **(2) The presentation deck (required)** — `deck/plenitude-voice-to-retention.html`.
  Leads with the business outcome, quantifies impact in the buyer's KPIs (churn %,
  margin), frames value for exec sponsor **and** the retention domain owner. Submit
  as the committed HTML file in the repo (or export/share per the form's options).
- **(3) Conversation ID (optional)** — this Claude Code session, if the build gets
  flagged and they ask.

## Pre-submission gate

- [ ] `git init` this folder, commit, push to GitHub; confirm the repo is readable.
- [ ] Re-run `python data/run_local_pipeline.py` so `evidence/` is fresh.
- [ ] Skim the deck once in a browser (light + dark).
- [ ] Complete the attestation (own work; AI tools used as documented in `docs/AI_USAGE.md`).
- [ ] Rehearse the ~20–30 min roleplay: tell-show-tell, be ready for both the
      business stakeholder and the technical persona (objection prep in the deck's
      "decisions & trade-offs" slide).

## Do NOT include
- No real customer data (this build uses only synthetic data). ✔
- Do not use the Solution Generator, share/reuse another FE's build. ✔
