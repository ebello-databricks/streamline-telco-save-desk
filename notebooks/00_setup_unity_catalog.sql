-- Databricks notebook source
-- MAGIC %md
-- MAGIC # 00 · Unity Catalog — govern the journey
-- MAGIC **FE Bar stage: Unity Catalog (govern it).**
-- MAGIC
-- MAGIC One governed namespace for the Streamline Telco *Save Desk*: a `raw` → `silver` → `gold`
-- MAGIC medallion in one catalog, a managed **Volume** for the synthetic landing files, a tag on
-- MAGIC the sensitive care-call transcripts, a **column mask** so only the data team sees raw text,
-- MAGIC and least-privilege grants (retention team reads gold only).
-- MAGIC
-- MAGIC > All data is **synthetic** (`data/generate_synthetic_data.py`). Streamline Telco is fictional.

-- COMMAND ----------

CREATE CATALOG IF NOT EXISTS streamline_telco
  COMMENT 'FE Bar — Streamline Telco Save Desk. Synthetic postpaid churn use case.';

CREATE SCHEMA IF NOT EXISTS streamline_telco.raw    COMMENT 'Bronze — raw synthetic landing data';
CREATE SCHEMA IF NOT EXISTS streamline_telco.silver COMMENT 'Silver — conformed + Gen AI enriched entities';
CREATE SCHEMA IF NOT EXISTS streamline_telco.gold   COMMENT 'Gold — features, churn scores, save list';

CREATE VOLUME IF NOT EXISTS streamline_telco.raw.landing
  COMMENT 'Drop zone: subscribers / contracts / usage / care_calls / churn_labels';

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Governance — classification, masking, access
-- MAGIC Run after `01_ingest_lakeflow` and `02_genai_enrichment` have created the tables.

-- COMMAND ----------

-- Discoverable classification on the free-text column
ALTER TABLE streamline_telco.silver.care_calls_enriched
  ALTER COLUMN transcript SET TAGS ('classification' = 'sensitive', 'contains' = 'free_text_pii');

-- Column mask: only the data team sees raw transcripts; everyone else sees a redaction
CREATE OR REPLACE FUNCTION streamline_telco.silver.mask_transcript(t STRING)
  RETURN CASE WHEN is_account_group_member('streamline-data-team') THEN t ELSE '[REDACTED]' END;
ALTER TABLE streamline_telco.silver.care_calls_enriched
  ALTER COLUMN transcript SET MASK streamline_telco.silver.mask_transcript;

-- Least privilege: retention team reads GOLD only (adjust group names to your workspace)
GRANT USE CATALOG ON CATALOG streamline_telco TO `streamline-retention`;
GRANT USE SCHEMA, SELECT ON SCHEMA streamline_telco.gold TO `streamline-retention`;
GRANT USE SCHEMA, SELECT ON SCHEMA streamline_telco.silver TO `streamline-data-team`;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC Lineage from `raw.landing` → `silver.*` → `gold.save_list` → Lakebase → App is captured
-- MAGIC automatically by Unity Catalog (Catalog Explorer → Lineage). No extra code needed.
