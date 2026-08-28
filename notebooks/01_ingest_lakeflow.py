# Databricks notebook source
# MAGIC %md
# MAGIC # 01 · Lakeflow — ingest the raw data
# MAGIC **FE Bar stage: Lakeflow (ingest the raw data).**
# MAGIC
# MAGIC A **Lakeflow Declarative Pipeline** (formerly Delta Live Tables) that ingests the
# MAGIC synthetic landing files from the Unity Catalog Volume into **bronze** (`raw.*`),
# MAGIC then conforms and quality-checks them into **silver** (`silver.*`).
# MAGIC
# MAGIC Attach this notebook to a Lakeflow pipeline with target catalog `plenitude_febar`.
# MAGIC Bronze uses **Auto Loader** so new dropped files are picked up incrementally.

# COMMAND ----------

import dlt
from pyspark.sql import functions as F

VOLUME = "/Volumes/plenitude_febar/raw/landing"

# ---------------------------------------------------------------- BRONZE
def _bronze(name):
    @dlt.table(name=f"bronze_{name}", comment=f"Raw {name} (Auto Loader, synthetic)")
    def _t():
        return (spark.readStream.format("cloudFiles")
                .option("cloudFiles.format", "parquet")
                .option("cloudFiles.inferColumnTypes", "true")
                .load(f"{VOLUME}/{name}.parquet")
                .withColumn("_ingested_at", F.current_timestamp()))
    return _t

for _n in ["customers", "consumption", "contracts", "calls", "churn_labels"]:
    _bronze(_n)

# ---------------------------------------------------------------- SILVER
@dlt.table(comment="Conformed customers")
@dlt.expect_or_drop("valid_id", "customer_id IS NOT NULL")
@dlt.expect("plausible_bill", "monthly_bill_eur BETWEEN 5 AND 5000")
def silver_customers():
    return (dlt.read("bronze_customers")
            .withColumn("contract_end_date", F.to_date("contract_end_date"))
            .dropDuplicates(["customer_id"]))

@dlt.table(comment="Conformed monthly consumption")
@dlt.expect_or_drop("valid", "customer_id IS NOT NULL AND bill_amount_eur >= 0")
def silver_consumption():
    return (dlt.read("bronze_consumption")
            .withColumn("month", F.to_date("month")))

@dlt.table(comment="Active contracts")
def silver_contracts():
    return (dlt.read("bronze_contracts")
            .withColumn("start_date", F.to_date("start_date"))
            .withColumn("end_date", F.to_date("end_date")))

@dlt.table(comment="Contact-centre calls with transcripts (transcript = sensitive)")
@dlt.expect_or_drop("has_transcript", "transcript IS NOT NULL AND length(transcript) > 0")
def silver_calls():
    return (dlt.read("bronze_calls")
            .withColumn("call_ts", F.to_timestamp("call_ts"))
            .withColumn("call_date", F.to_date("call_ts")))

@dlt.table(comment="Ground-truth churn labels (90d)")
def silver_churn_labels():
    return dlt.read("bronze_churn_labels").select("customer_id", "churned_next_90d")

# COMMAND ----------

# MAGIC %md
# MAGIC **Data quality is enforced in the pipeline** (`@dlt.expect*`), so bad rows are
# MAGIC dropped/flagged and surfaced in the pipeline's data-quality dashboard — evidence
# MAGIC the ingestion actually ran and enforced contracts.
# MAGIC
# MAGIC Next: **`02_genai_enrichment`** turns `silver_calls.transcript` into churn signal.
