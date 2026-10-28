# Databricks notebook source
# MAGIC %md
# MAGIC # 04 · Lakebase — operational serving
# MAGIC **FE Bar stage: Lakebase (operational serving).**
# MAGIC
# MAGIC The Save Desk app is an **operational** workload: an agent opens a subscriber
# MAGIC (point lookup, milliseconds) and records the outcome (transactional insert).
# MAGIC `gold.save_list` is mirrored into **Lakebase** (managed Postgres) with a **synced table**,
# MAGIC and a `save_actions` table receives the agents' write-back. Outcomes flow back to the
# MAGIC lakehouse to retrain the model on what actually saved customers.

# COMMAND ----------

from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
INSTANCE = "streamline-save-desk"     # created by databricks.yml (database_instances)

w.database.create_synced_database_table(
    name="streamline_telco.gold.save_list_synced",
    spec={
        "source_table_full_name": "streamline_telco.gold.save_list",
        "primary_key_columns": ["subscriber_id"],
        "scheduling_policy": "TRIGGERED",          # refreshed after each nightly scoring run
        "database_instance_name": INSTANCE,
    },
)
print("synced table requested: gold.save_list -> Lakebase")

# COMMAND ----------

import uuid, psycopg
inst = w.database.get_database_instance(INSTANCE)
cred = w.database.generate_database_credential(request_id=str(uuid.uuid4()), instance_names=[INSTANCE])
me = w.current_user.me().user_name

with psycopg.connect(host=inst.read_write_dns, dbname="databricks_postgres", user=me,
                     password=cred.token, sslmode="require") as conn:
    conn.execute("""
    CREATE TABLE IF NOT EXISTS save_actions (
        action_id     BIGSERIAL PRIMARY KEY,
        subscriber_id TEXT NOT NULL,
        agent_id      TEXT,
        offer         TEXT,
        outcome       TEXT CHECK (outcome IN ('accepted','declined','callback','no_answer')),
        notes         TEXT,
        created_at    TIMESTAMPTZ DEFAULT now())""")
    row = conn.execute("SELECT subscriber_id, churn_probability, next_best_offer "
                       "FROM save_list_synced ORDER BY value_at_risk_eur DESC LIMIT 1").fetchone()
    conn.execute("INSERT INTO save_actions(subscriber_id, agent_id, offer, outcome) VALUES (%s,%s,%s,'accepted')",
                 (row[0], "AG017", row[2]))
    print(row, conn.execute("SELECT count(*) FROM save_actions").fetchone())

# COMMAND ----------

# MAGIC %md
# MAGIC Local mirror (SQLite stand-in, same schema): `evidence/model_run_output.txt` step `[6 serve]`
# MAGIC — 20,000 rows loaded, 500 point lookups, one agent write-back row.
# MAGIC `save_actions` is registered back into UC (Lakebase catalog) for the outcome-feedback loop.
