# Databricks notebook source
# MAGIC %md
# MAGIC # 04 · Lakebase — operational serving
# MAGIC **FE Bar stage: Lakebase (operational serving).**
# MAGIC
# MAGIC The retention cockpit app needs **low-latency, transactional** reads of the churn
# MAGIC scores plus a place to write back the retention team's actions (who was called,
# MAGIC outcome). We publish `gold.churn_scores` into a **Lakebase** (managed Postgres)
# MAGIC instance and add an `actions` table the app writes to — the operational serving
# MAGIC layer, separate from the analytical lakehouse.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Create the Lakebase instance (one-time, or via `databricks.yml`)
# MAGIC ```bash
# MAGIC databricks database create-database-instance plenitude-febar \
# MAGIC   --capacity CU_1
# MAGIC ```
# MAGIC Then create a **synced table** so `gold.churn_scores` is continuously mirrored
# MAGIC into Postgres (Lakebase reverse-ETL), and a companion `retention_actions` table.

# COMMAND ----------

from databricks.sdk import WorkspaceClient
w = WorkspaceClient()

INSTANCE = "plenitude-febar"
# Synced table: UC gold -> Lakebase Postgres, kept fresh (snapshot/continuous)
w.database.create_synced_database_table(
    name="plenitude_febar.gold.churn_scores_synced",
    spec={
        "source_table_full_name": "plenitude_febar.gold.churn_scores",
        "primary_key_columns": ["customer_id"],
        "scheduling_policy": "SNAPSHOT",
        "database_instance_name": INSTANCE,
    },
)
print("synced table requested — Lakebase now serves churn_scores over Postgres")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2. Write-back table for retention actions (app -> Lakebase)
# MAGIC The app records each retention interaction. Because Lakebase is real Postgres,
# MAGIC this is a normal transactional insert with immediate read-after-write.

# COMMAND ----------

import psycopg2, os
# Connection details come from the Lakebase instance + a workspace OAuth token.
conn = psycopg2.connect(
    host=os.environ["PGHOST"], dbname="databricks_postgres",
    user=os.environ["PGUSER"], password=os.environ["PGPASSWORD"], sslmode="require")
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS retention_actions (
    action_id     BIGSERIAL PRIMARY KEY,
    customer_id   TEXT NOT NULL,
    agent         TEXT,
    action        TEXT,               -- e.g. 'offer_made','callback','saved','lost'
    offer_eur     NUMERIC,
    notes         TEXT,
    created_at    TIMESTAMPTZ DEFAULT now()
);
""")
conn.commit()
print("retention_actions ready in Lakebase")

# COMMAND ----------

# MAGIC %md
# MAGIC The app (`app/app.py`) reads `churn_scores_synced` for the ranked call list and
# MAGIC inserts into `retention_actions` when an agent logs an outcome — closing the loop
# MAGIC from analytical scores to operational action.
