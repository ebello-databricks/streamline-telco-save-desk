# Deploy runbook — lean spine on e2-demo-field-eng

The goal: a **simple, functional, demo-able** build that won't get blocked mid-deploy.
We stand up the reliable **spine** first (UC + data + live Gen AI + App + Genie), and
add Lakebase / the DLT pipeline / the full DAB as **Tier-2 iterations** only if wanted.

> **Key simplification.** The gold tables were already computed by the local pipeline
> (`data/run_local_pipeline.py`, evidence committed). We publish those straight to UC,
> so the App / Genie / dashboard have real data immediately — no need to run all five
> notebooks in the workspace. Gen AI runs **live** on the transcripts so the AI is real.

## Live resources (e2-demo-field-eng · workspace 1444828305810485)

| Resource | Value |
|---|---|
| Profile | `e2-demo` |
| SQL warehouse | `plenitude-febar-wh` · id `c8d3657be7ec0f0f` (serverless, auto-stop 10m) |
| Catalog | `plenitude_febar` (`raw` / `silver` / `gold` + volume `raw.landing`) |
| App | `plenitude-retention` · https://plenitude-retention-1444828305810485.aws.databricksapps.com |
| App service principal | `ffd2d637-8a99-46c9-b012-2fa227b404a3` |
| Genie space | *created manually — see step 6* |

## Prereqs
```bash
databricks auth login --profile e2-demo      # OAuth, opens a browser
# helper used below (no SDK needed): /tmp/febar/run_sql.py runs SQL via the CLI
```

## 1 · Catalog + medallion + volume
```bash
python3 /tmp/febar/run_sql.py \
  "CREATE CATALOG IF NOT EXISTS plenitude_febar" \
  "CREATE SCHEMA IF NOT EXISTS plenitude_febar.raw" \
  "CREATE SCHEMA IF NOT EXISTS plenitude_febar.silver" \
  "CREATE SCHEMA IF NOT EXISTS plenitude_febar.gold" \
  "CREATE VOLUME IF NOT EXISTS plenitude_febar.raw.landing"
```

## 2 · Upload synthetic data to the volume
```bash
L=dbfs:/Volumes/plenitude_febar/raw/landing
cd data/output
for f in customers consumption contracts calls churn_labels gold_churn_scores gold_customer_features; do
  databricks fs cp "$f.parquet" "$L/$f.parquet" --overwrite -p e2-demo
done
```

## 3 · Create tables from the parquet
`raw.*` entities, `silver.silver_calls` (with a derived `call_date`), and the two
gold tables. See `run_sql.py` calls in the session, or re-run the `CREATE OR REPLACE
TABLE ... read_files('<volume path>', format=>'parquet')` statements.

## 4 · Live Gen AI enrichment (the differentiator)
Runs `ai_analyze_sentiment` / `ai_classify` / `ai_query` on real Italian transcripts →
`silver.calls_enriched`. Sample of 800 for speed; **remove `LIMIT 800` for the full run.**
```sql
CREATE OR REPLACE TABLE plenitude_febar.silver.calls_enriched AS
SELECT call_id, customer_id, call_ts, call_date, queue AS intent_source, duration_sec, transcript,
  ai_analyze_sentiment(transcript) AS sentiment,
  ai_classify(transcript, ARRAY('billing','retention','technical','commercial','self_service')) AS intent,
  CAST(ai_query('databricks-meta-llama-3-3-70b-instruct',
    CONCAT('Does this energy-customer call express intent to switch supplier or cancel the contract? Answer only 1 or 0.\n', transcript)) AS INT) AS churn_signal,
  ai_query('databricks-meta-llama-3-3-70b-instruct',
    CONCAT('Summarise this customer call in <=12 words, in English:\n', transcript)) AS summary
FROM plenitude_febar.silver.silver_calls
WHERE length(transcript) > 0 LIMIT 800;
```
Verified result (800 sample): negative 347 (86% churn-signal), neutral 337, positive 116.

## 5 · Databricks App (retention cockpit)
The app reads `gold.churn_scores` from UC via the warehouse, authed as its own service
principal (no Lakebase needed). Grants + deploy:
```bash
SP=ffd2d637-8a99-46c9-b012-2fa227b404a3
python3 /tmp/febar/run_sql.py \
  "GRANT USE CATALOG ON CATALOG plenitude_febar TO \`$SP\`" \
  "GRANT USE SCHEMA, SELECT, CREATE TABLE ON SCHEMA plenitude_febar.gold TO \`$SP\`" \
  "GRANT USE SCHEMA, SELECT ON SCHEMA plenitude_febar.silver TO \`$SP\`"
databricks api patch /api/2.0/permissions/warehouses/c8d3657be7ec0f0f -p e2-demo \
  --json '{"access_control_list":[{"service_principal_name":"'"$SP"'","permission_level":"CAN_USE"}]}'

databricks workspace import-dir ./app \
  /Workspace/Users/emmanuele.bello@databricks.com/plenitude-retention-src --overwrite -p e2-demo
databricks apps deploy plenitude-retention \
  --source-code-path /Workspace/Users/emmanuele.bello@databricks.com/plenitude-retention-src -p e2-demo
```

## 6 · Genie space (2-min manual step)
The direct-create API now needs a `serialized_space` blob, so create it in the UI:
1. **New → Genie space**, warehouse = `plenitude-febar-wh`.
2. Add tables: `plenitude_febar.gold.churn_scores`, `gold.customer_features`, `silver.calls_enriched`.
3. Paste `instructions` + `sample_questions` from `genie/genie_space_config.json`.
4. Test: *"Quali clienti in Lombardia con tariffa variabile hanno parlato di cambio fornitore?"*

## Tier-2 iterations (only if you want them)
- **Real DLT pipeline** — run `notebooks/01_ingest_lakeflow.py` as a Lakeflow pipeline
  instead of the direct `read_files` load in step 3.
- **Lakebase serving + write-back** — `notebooks/04_lakebase_serving.py`; set `PGHOST`/`PGUSER`/
  `PGPASSWORD` on the app and it switches to Postgres automatically.
- **AI/BI dashboard** — deploy `dashboard/churn_dashboard.lvdash.json` (warehouse `c8d3657be7ec0f0f`).
- **Full DAB** — `databricks bundle deploy -t dev` once the spine is proven.

## Teardown
```bash
databricks apps delete plenitude-retention -p e2-demo
python3 /tmp/febar/run_sql.py "DROP CATALOG IF EXISTS plenitude_febar CASCADE"
databricks warehouses delete c8d3657be7ec0f0f -p e2-demo
```
