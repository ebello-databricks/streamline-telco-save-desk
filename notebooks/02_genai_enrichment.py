# Databricks notebook source
# MAGIC %md
# MAGIC # 02 · Gen AI — make the voice intelligent
# MAGIC **FE Bar stage: ML or Gen AI (make it intelligent) — part 1, Gen AI.**
# MAGIC
# MAGIC Every contact-centre call transcript is enriched with **sentiment**, **intent**,
# MAGIC a **churn signal**, and a one-line **summary** using Databricks built-in
# MAGIC **Foundation Model API** SQL functions — no model to host, no data leaves UC.
# MAGIC
# MAGIC These voice-derived features become the churn model's **top predictors**
# MAGIC (see `03_churn_model`): `churn_mentions` and `avg_sentiment` rank #1 and top-8.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Sentiment + intent classification + churn-intent detection in pure SQL.
# MAGIC -- ai_analyze_sentiment / ai_classify / ai_query call the built-in FM API.
# MAGIC CREATE OR REPLACE TABLE plenitude_febar.silver.calls_enriched AS
# MAGIC SELECT
# MAGIC   call_id, customer_id, call_ts, call_date, queue AS intent_source, duration_sec,
# MAGIC   transcript,
# MAGIC   ai_analyze_sentiment(transcript)                              AS sentiment,
# MAGIC   ai_classify(transcript,
# MAGIC     ARRAY('billing','retention','technical','commercial','self_service')) AS intent,
# MAGIC   CAST(ai_query(
# MAGIC     'databricks-meta-llama-3-3-70b-instruct',
# MAGIC     CONCAT('Does this energy-customer call express intent to switch supplier or ',
# MAGIC            'cancel the contract? Answer only 1 or 0.\n', transcript)
# MAGIC   ) AS INT)                                                      AS churn_signal,
# MAGIC   ai_query(
# MAGIC     'databricks-meta-llama-3-3-70b-instruct',
# MAGIC     CONCAT('Summarise this customer call in <=12 words, in English:\n', transcript)
# MAGIC   )                                                             AS summary
# MAGIC FROM plenitude_febar.silver.silver_calls;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- sanity check the enrichment (this cell's output = execution evidence)
# MAGIC SELECT sentiment, count(*) AS n,
# MAGIC        round(avg(churn_signal), 3) AS churn_signal_rate
# MAGIC FROM plenitude_febar.silver.calls_enriched
# MAGIC GROUP BY sentiment ORDER BY n DESC;

# COMMAND ----------

# MAGIC %md
# MAGIC ### Note on the local evidence
# MAGIC The committed run evidence (`evidence/model_run_output.txt`) was produced by the
# MAGIC local mirror (`data/run_local_pipeline.py`), which reproduces this enrichment with
# MAGIC a deterministic Italian lexicon so results are byte-reproducible offline. In the
# MAGIC workspace, the two `ai_*` functions above do the same job with the FM API.
# MAGIC Observed sentiment mix on the synthetic set: **neutral 62.7% · negative 30.3% · positive 7.0%**,
# MAGIC with **3,650** calls flagged as churn-signal.
