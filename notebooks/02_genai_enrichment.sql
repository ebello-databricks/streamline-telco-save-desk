-- Databricks notebook source
-- MAGIC %md
-- MAGIC # 02 · Gen AI — turn every care call into a churn signal
-- MAGIC **FE Bar stage: ML or Gen AI (make it intelligent).**
-- MAGIC
-- MAGIC Databricks **AI Functions** run the Foundation Model API straight from SQL, governed by
-- MAGIC Unity Catalog — no model to host, transcripts never leave the platform.
-- MAGIC - `ai_analyze_sentiment` → sentiment
-- MAGIC - `ai_classify` → intent (network / billing / retention / device / general)
-- MAGIC - `ai_query` → switch intent (0/1): *"is this customer threatening to leave?"*
-- MAGIC
-- MAGIC Incremental: only calls not yet enriched are processed, so daily cost scales with new calls.

-- COMMAND ----------

CREATE TABLE IF NOT EXISTS streamline_telco.silver.care_calls_enriched (
  call_id STRING, subscriber_id STRING, call_ts TIMESTAMP, duration_sec INT, transcript STRING,
  sentiment STRING, intent STRING, switch_intent INT, enriched_at TIMESTAMP);

-- COMMAND ----------

INSERT INTO streamline_telco.silver.care_calls_enriched
SELECT c.call_id, c.subscriber_id, c.call_ts, c.duration_sec, c.transcript,
  ai_analyze_sentiment(c.transcript)                                              AS sentiment,
  ai_classify(c.transcript, ARRAY('network','billing','retention','device','general')) AS intent,
  COALESCE(TRY_CAST(TRIM(ai_query('databricks-meta-llama-3-3-70b-instruct',
       CONCAT('You work for a mobile operator. Does this customer care call show intent to leave, ',
              'cancel, port the number or switch provider? Answer only 1 or 0.\nCall: ', c.transcript))) AS INT), 0)
                                                                                  AS switch_intent,
  current_timestamp()                                                             AS enriched_at
FROM streamline_telco.silver.care_calls c
LEFT ANTI JOIN streamline_telco.silver.care_calls_enriched e ON c.call_id = e.call_id;

-- COMMAND ----------

-- Quality check: does the LLM intent agree with the IVR queue the caller picked?
SELECT intent, sentiment, COUNT(*) calls, ROUND(AVG(switch_intent) * 100, 1) pct_switch_intent
FROM streamline_telco.silver.care_calls_enriched
GROUP BY ALL ORDER BY calls DESC;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC Local, reproducible mirror of this step (lexicon stand-in for the LLM) and its output:
-- MAGIC `evidence/model_run_output.txt` step `[2 gen ai]` — 13,749 calls, 95.0% intent agreement
-- MAGIC with the IVR queue. In `03_churn_model` the ablation shows these call features add
-- MAGIC **+0.053 ROC-AUC** and lift top-decile precision from 0.42 to 0.56.
