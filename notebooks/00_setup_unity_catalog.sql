-- Databricks notebook source
-- MAGIC %md
-- MAGIC # 00 · Unity Catalog — govern the journey
-- MAGIC **FE Bar stage: Unity Catalog (govern it).**
-- MAGIC
-- MAGIC Creates the governed namespace for the Plenitude *Voice-to-Retention* build:
-- MAGIC a three-tier medallion (`raw` → `silver` → `gold`) inside one catalog, a
-- MAGIC managed **Volume** for the raw synthetic landing files, and grants/tags so
-- MAGIC the retention team can read gold while raw call transcripts stay restricted.
-- MAGIC
-- MAGIC > All data here is **synthetic** (see `data/generate_synthetic_data.py`). No real Plenitude / Eni customer data is used.

-- COMMAND ----------

CREATE CATALOG IF NOT EXISTS plenitude_febar
  COMMENT 'FE Bar — Plenitude Voice-to-Retention. Synthetic B2C energy retail churn use case.';

CREATE SCHEMA IF NOT EXISTS plenitude_febar.raw    COMMENT 'Bronze — raw synthetic landing tables';
CREATE SCHEMA IF NOT EXISTS plenitude_febar.silver COMMENT 'Silver — cleaned + enriched (Gen AI) entities';
CREATE SCHEMA IF NOT EXISTS plenitude_febar.gold   COMMENT 'Gold — features, churn scores, serving views';

-- Managed volume: where the generated parquet/csv land before Lakeflow ingests them
CREATE VOLUME IF NOT EXISTS plenitude_febar.raw.landing
  COMMENT 'Drop zone for synthetic customers/consumption/contracts/calls/churn_labels';

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Governance — data classification & access
-- MAGIC Call transcripts are the sensitive asset (free text). Tag them, and grant the
-- MAGIC retention analyst group read on **gold only**, not on raw transcripts.

-- COMMAND ----------

-- Tag the sensitive column so it is discoverable + policy-enforceable
ALTER TABLE plenitude_febar.silver.calls_enriched
  ALTER COLUMN transcript SET TAGS ('classification' = 'sensitive', 'contains' = 'free_text');

-- Least-privilege grants (adjust group names to your workspace)
GRANT USE CATALOG ON CATALOG plenitude_febar TO `account users`;
GRANT USE SCHEMA, SELECT ON SCHEMA plenitude_febar.gold TO `account users`;
-- raw + silver (transcripts) restricted to the data team
-- GRANT USE SCHEMA, SELECT ON SCHEMA plenitude_febar.silver TO `plenitude-data-team`;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC Next: **`01_ingest_lakeflow`** ingests the volume into `raw.*` and conforms to `silver.*`.
