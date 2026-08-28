# Databricks notebook source
# MAGIC %md
# MAGIC # 05 · Genie Room — make it queryable in natural language
# MAGIC **FE Bar stage: Genie Room (make it queryable in natural language).**
# MAGIC
# MAGIC Creates a **Genie space** over the gold tables so a retention manager can ask, in
# MAGIC plain Italian or English:
# MAGIC - *"Quali clienti in Lombardia con tariffa variabile hanno parlato di cambio fornitore?"*
# MAGIC - *"Show the top 20 critical-risk dual-fuel customers whose bill rose more than 15%."*
# MAGIC - *"What's the churn rate by region and how much annual revenue is in the High band?"*
# MAGIC
# MAGIC The space is defined declaratively in `genie/genie_space_config.json` and created
# MAGIC via the Genie API. Curated sample questions + column descriptions steer the model.

# COMMAND ----------

import json, requests
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
host = w.config.host
token = w.config.token

cfg = json.load(open("../genie/genie_space_config.json"))

resp = requests.post(
    f"{host}/api/2.0/genie/spaces",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "title": cfg["title"],
        "description": cfg["description"],
        "warehouse_id": cfg["warehouse_id"],   # set to your SQL warehouse id
        "table_identifiers": cfg["tables"],
        "instructions": cfg["instructions"],
        "sample_questions": cfg["sample_questions"],
    },
)
print(resp.status_code, resp.text[:400])

# COMMAND ----------

# MAGIC %md
# MAGIC ### Ask the space programmatically (what the app's "Ask Genie" box calls)
# MAGIC ```python
# MAGIC conv = w.genie.start_conversation_and_wait(
# MAGIC     space_id, "Top 20 critical customers in Lombardia who mentioned switching")
# MAGIC for a in conv.attachments:
# MAGIC     print(a.query.query, a.query.description)  # the SQL Genie generated + answer
# MAGIC ```
# MAGIC The generated SQL + result is committed as evidence in `evidence/query_results.md`.
