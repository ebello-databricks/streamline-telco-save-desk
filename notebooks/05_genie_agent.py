# Databricks notebook source
# MAGIC %md
# MAGIC # 05 · Genie agent — ask the save list in plain English
# MAGIC **FE Bar stage: Genie Agent (make it queryable in natural language).**
# MAGIC
# MAGIC A Genie space over the gold tables lets the Head of Retention and regional managers ask:
# MAGIC - *"How much annual revenue sits in the High and Critical bands?"*
# MAGIC - *"Which region has the most at-risk subscribers because of network problems?"*
# MAGIC - *"Show the 10 subscribers with the highest value at risk and what we should offer them."*
# MAGIC
# MAGIC Definition: `genie/genie_space_config.json` (tables, instructions, sample questions,
# MAGIC trusted SQL). Create it in the UI (New → Genie space) or via the API below, then query it
# MAGIC with the Conversation API — the same call the app's "Ask Genie" box makes.

# COMMAND ----------

import json
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
cfg = json.load(open("../genie/genie_space_config.json"))
dbutils.widgets.text("space_id", cfg.get("space_id", ""), "Genie space id")
SPACE_ID = dbutils.widgets.get("space_id")
assert SPACE_ID, "Create the Genie space first (see markdown above) and pass its id"

for q in cfg["sample_questions"][:3]:
    msg = w.genie.start_conversation_and_wait(SPACE_ID, q)
    for a in msg.attachments or []:
        if a.query:
            print("Q:", q, "\nSQL:", a.query.query, "\n")
        if a.text:
            print("A:", a.text.content, "\n")

# COMMAND ----------

# MAGIC %md
# MAGIC Answers to the same questions, computed as SQL over gold on the synthetic data, are committed
# MAGIC in `evidence/query_results.md`.
