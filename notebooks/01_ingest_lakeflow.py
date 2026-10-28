# Databricks notebook source
# MAGIC %md
# MAGIC # 01 · Lakeflow — ingest the raw data
# MAGIC **FE Bar stage: Lakeflow (ingest the raw data).**
# MAGIC
# MAGIC A **Lakeflow Declarative Pipeline** that ingests the synthetic landing files from the UC
# MAGIC Volume into **bronze** with Auto Loader (incremental — new daily drops are picked up
# MAGIC automatically), then conforms and quality-checks them into **silver** with expectations.
# MAGIC
# MAGIC Target catalog `streamline_telco`, schema `silver` (see `databricks.yml`).
# MAGIC In production the same bronze tables are fed by Lakeflow Connect / Kafka from the
# MAGIC billing system, the network probe feed and the contact-centre platform.

# COMMAND ----------

import dlt
from pyspark.sql import functions as F

VOLUME = "/Volumes/streamline_telco/raw/landing"


def _bronze(name):
    @dlt.table(name=f"bronze_{name}", comment=f"Raw {name} (Auto Loader, synthetic)")
    def _t():
        return (spark.readStream.format("cloudFiles")
                .option("cloudFiles.format", "parquet")
                .option("cloudFiles.inferColumnTypes", "true")
                .load(f"{VOLUME}/{name}/")
                .withColumn("_ingested_at", F.current_timestamp()))
    return _t


for _n in ["subscribers", "contracts", "usage", "care_calls", "churn_labels"]:
    _bronze(_n)

# COMMAND ----------

@dlt.table(comment="Conformed postpaid subscribers")
@dlt.expect_or_drop("valid_id", "subscriber_id IS NOT NULL")
def subscribers():
    return dlt.read("bronze_subscribers").dropDuplicates(["subscriber_id"])


@dlt.table(comment="Active contracts / commitments")
@dlt.expect_or_drop("positive_price", "monthly_price_eur > 0")
def contracts():
    return (dlt.read("bronze_contracts")
            .withColumn("start_date", F.to_date("start_date"))
            .withColumn("commitment_end_date", F.to_date("commitment_end_date")))


@dlt.table(comment="Monthly usage + network experience")
@dlt.expect_or_drop("plausible_bill", "bill_amount_eur > 0 AND bill_amount_eur < 1000")
@dlt.expect("non_negative_drops", "dropped_calls >= 0")
def usage():
    return dlt.read("bronze_usage").withColumn("month", F.to_date("month"))


@dlt.table(comment="Care calls with transcripts (transcript = sensitive)")
@dlt.expect_or_drop("has_transcript", "transcript IS NOT NULL AND length(transcript) > 0")
def care_calls():
    return dlt.read("bronze_care_calls").withColumn("call_ts", F.to_timestamp("call_ts"))


@dlt.table(comment="Ground-truth churn labels (port-out within 60 days)")
def churn_labels():
    return dlt.read("bronze_churn_labels").select("subscriber_id", "churned_next_60d")

# COMMAND ----------

# MAGIC %md
# MAGIC Expectations drop or flag bad rows and surface them in the pipeline's data-quality view.
# MAGIC Local mirror of these rules + row counts: `evidence/model_run_output.txt` step `[1 silver]`.
# MAGIC Next: **`02_genai_enrichment`**.
