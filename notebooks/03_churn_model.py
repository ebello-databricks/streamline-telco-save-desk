# Databricks notebook source
# MAGIC %md
# MAGIC # 03 · ML — churn model + save list
# MAGIC **FE Bar stage: ML or Gen AI (make it intelligent).**
# MAGIC
# MAGIC 1. Build `gold.subscriber_features`: network experience + billing trend + contract + the
# MAGIC    **Gen AI care-call features** from `02`.
# MAGIC 2. Train a GradientBoosting churn model, tracked in **MLflow**, registered to **Unity Catalog**.
# MAGIC 3. Score every subscriber → `gold.save_list` with risk band, value at risk, primary driver,
# MAGIC    next-best-offer and an `ai_query` talk track for the agent.
# MAGIC
# MAGIC Same logic as `data/run_local_pipeline.py` (steps 3–5); run output in `evidence/`.

# COMMAND ----------

import mlflow, pandas as pd, numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import roc_auc_score, average_precision_score
import importlib.util, sys

CAT = "streamline_telco"
mlflow.set_registry_uri("databricks-uc")

# Reuse the exact feature/offer logic from the repo so local evidence == workspace run
spec = importlib.util.spec_from_file_location("pipe", "../data/run_local_pipeline.py")
pipe = importlib.util.module_from_spec(spec); spec.loader.exec_module(pipe)

subs = spark.table(f"{CAT}.silver.subscribers").toPandas()
contr = spark.table(f"{CAT}.silver.contracts").toPandas()
usage = spark.table(f"{CAT}.silver.usage").toPandas()
enr = (spark.table(f"{CAT}.silver.care_calls_enriched")
       .selectExpr("call_id", "subscriber_id", "intent", "sentiment", "switch_intent",
                   "CASE sentiment WHEN 'negative' THEN -0.6 WHEN 'positive' THEN 0.7 ELSE 0.05 END AS sentiment_score")
       .toPandas())
labels = spark.table(f"{CAT}.silver.churn_labels").toPandas()

feats = pipe.build_features(subs, contr, usage, enr).merge(labels, on="subscriber_id")
spark.createDataFrame(feats).write.mode("overwrite").option("overwriteSchema", "true") \
     .saveAsTable(f"{CAT}.gold.subscriber_features")

# COMMAND ----------

X, y = feats[pipe.FEATURES], feats["churned_next_60d"]
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=7, stratify=y)

with mlflow.start_run(run_name="save_desk_gbm") as run:
    clf = GradientBoostingClassifier(n_estimators=250, max_depth=3, learning_rate=0.06,
                                     subsample=0.9, random_state=7).fit(Xtr, ytr)
    p = clf.predict_proba(Xte)[:, 1]
    k = int(len(p) * 0.10)
    top_prec = yte.iloc[np.argsort(-p)[:k]].mean()
    mlflow.log_metrics({"roc_auc": roc_auc_score(yte, p), "pr_auc": average_precision_score(yte, p),
                        "precision_top_decile": top_prec, "lift_top_decile": top_prec / yte.mean()})
    mlflow.sklearn.log_model(clf, "model", input_example=Xte.head(5),
                             registered_model_name=f"{CAT}.gold.save_desk_churn")
print(run.info.run_id)

# COMMAND ----------

feats["churn_probability"] = clf.predict_proba(X)[:, 1].round(4)
feats["risk_band"] = pd.cut(feats.churn_probability, [-0.01, 0.2, 0.4, 0.6, 1.01],
                            labels=["Low", "Medium", "High", "Critical"]).astype(str)
feats["driver"] = feats.apply(pipe.primary_driver, axis=1)
feats["next_best_offer"] = feats.driver.map(lambda d: pipe.OFFERS[d][0])
feats["offer_cost_eur"] = feats.driver.map(lambda d: pipe.OFFERS[d][1])
feats["annual_value_eur"] = (feats.avg_bill_eur * 12).round(0)
feats["value_at_risk_eur"] = (feats.annual_value_eur * feats.churn_probability).round(0)
feats["top_reasons"] = feats.apply(lambda r: "; ".join(pipe.reasons(r)), axis=1)
cols = [c for c in ["subscriber_id", "region", "segment", "plan", "lines", "tenure_months", "avg_bill_eur",
        "annual_value_eur", "churn_probability", "risk_band", "value_at_risk_eur", "driver", "top_reasons",
        "next_best_offer", "offer_cost_eur", "dropped_calls_l2m", "dl_speed_l2m", "bill_trend_pct",
        "days_to_commitment_end", "switch_intent"]]
spark.createDataFrame(feats[cols]).write.mode("overwrite").option("overwriteSchema", "true") \
     .saveAsTable(f"{CAT}.gold.save_list")

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Gen AI talk track for the agent, only for the High/Critical subscribers (keeps token cost low)
# MAGIC ALTER TABLE streamline_telco.gold.save_list ADD COLUMNS (talk_track STRING);
# MAGIC MERGE INTO streamline_telco.gold.save_list t
# MAGIC USING (
# MAGIC   SELECT subscriber_id, ai_query('databricks-meta-llama-3-3-70b-instruct',
# MAGIC     CONCAT('Write a 2-sentence, empathetic opening for a retention agent calling a mobile customer. ',
# MAGIC            'Reasons they may leave: ', top_reasons, '. Offer to present: ', next_best_offer,
# MAGIC            '. No promises beyond the offer.')) AS talk_track
# MAGIC   FROM streamline_telco.gold.save_list WHERE risk_band IN ('High','Critical')
# MAGIC ) s ON t.subscriber_id = s.subscriber_id
# MAGIC WHEN MATCHED THEN UPDATE SET t.talk_track = s.talk_track;
# MAGIC
# MAGIC ALTER TABLE streamline_telco.gold.save_list SET TBLPROPERTIES (delta.enableChangeDataFeed = true);
