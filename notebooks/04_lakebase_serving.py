# Databricks notebook source
# MAGIC %md
# MAGIC # 04 · Lakebase — operational serving
# MAGIC **FE Bar stage: Lakebase (operational serving).**
# MAGIC
# MAGIC The Save Desk app is an **operational** workload: an agent opens a subscriber
# MAGIC (point lookup, milliseconds) and records the outcome (transactional insert).
# MAGIC `gold.save_list` is mirrored into **Lakebase** (managed Postgres) with a **synced table**,
# MAGIC and a `save_desk.save_actions` table receives the agents' write-back. Outcomes flow back
# MAGIC to the lakehouse to retrain the model on what actually saved customers.
# MAGIC
# MAGIC Idempotent: safe to run every night from the `save-desk-nightly` job.

# COMMAND ----------

# MAGIC %pip install "psycopg[binary]>=3.1" "databricks-sdk>=0.60"
# MAGIC %restart_python

# COMMAND ----------

import uuid, psycopg
from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import NotFound
from databricks.sdk.service.database import (SyncedDatabaseTable, SyncedTableSpec,
                                             SyncedTableSchedulingPolicy, NewPipelineSpec)

dbutils.widgets.text("app_sp_client_id", "", "App service principal client id")
APP_SP = dbutils.widgets.get("app_sp_client_id")

w = WorkspaceClient()
INSTANCE = "streamline-save-desk"     # created by databricks.yml (database_instances)
PG_DB = "databricks_postgres"
SYNCED = "streamline_telco.gold.save_list_synced"

# 1. Synced table: create once, then trigger a refresh after each nightly scoring run
try:
    st = w.database.get_synced_database_table(SYNCED)
    print("synced table exists")
except NotFound:
    st = w.database.create_synced_database_table(SyncedDatabaseTable(
        name=SYNCED,
        database_instance_name=INSTANCE,
        logical_database_name=PG_DB,
        spec=SyncedTableSpec(
            source_table_full_name="streamline_telco.gold.save_list",
            primary_key_columns=["subscriber_id"],
            scheduling_policy=SyncedTableSchedulingPolicy.TRIGGERED,
            create_database_objects_if_missing=True,
            new_pipeline_spec=NewPipelineSpec(storage_catalog="streamline_telco", storage_schema="gold"),
        )))
    print("synced table created: gold.save_list -> Lakebase (initial snapshot runs now)")

pipeline_id = (st.data_synchronization_status.pipeline_id
               if st.data_synchronization_status else None)
if pipeline_id:
    w.pipelines.start_update(pipeline_id)
    print("triggered refresh, pipeline", pipeline_id)

# COMMAND ----------

# 2. Write-back table + grants for the app's service principal
inst = w.database.get_database_instance(INSTANCE)
cred = w.database.generate_database_credential(request_id=str(uuid.uuid4()), instance_names=[INSTANCE])
me = w.current_user.me().user_name

with psycopg.connect(host=inst.read_write_dns, dbname=PG_DB, user=me,
                     password=cred.token, sslmode="require") as conn:
    conn.execute("CREATE SCHEMA IF NOT EXISTS save_desk")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS save_desk.save_actions (
        action_id     BIGSERIAL PRIMARY KEY,
        subscriber_id TEXT NOT NULL,
        agent_id      TEXT,
        offer         TEXT,
        outcome       TEXT CHECK (outcome IN ('accepted','declined','callback','no_answer')),
        notes         TEXT,
        created_at    TIMESTAMPTZ DEFAULT now())""")
    if APP_SP:
        # the app SP's Postgres role is created by the app's `lakebase` resource
        conn.execute(f'GRANT USAGE ON SCHEMA save_desk, gold TO "{APP_SP}"')
        conn.execute(f'GRANT SELECT ON gold.save_list_synced TO "{APP_SP}"')
        conn.execute(f'GRANT SELECT, INSERT ON save_desk.save_actions TO "{APP_SP}"')
        conn.execute(f'GRANT USAGE ON SEQUENCE save_desk.save_actions_action_id_seq TO "{APP_SP}"')
    print("save_actions rows so far:", conn.execute("SELECT count(*) FROM save_desk.save_actions").fetchone()[0])

# COMMAND ----------

# MAGIC %md
# MAGIC Local mirror (SQLite stand-in, same schema): `evidence/model_run_output.txt` step `[6 serve]`
# MAGIC — 20,000 rows loaded, 500 point lookups, one test write-back row.
# MAGIC `save_desk.save_actions` is registered back into UC (Lakebase catalog) for the outcome-feedback loop.
