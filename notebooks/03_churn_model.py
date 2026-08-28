# Databricks notebook source
# MAGIC %md
# MAGIC # 03 · ML — the churn model (GOLD)
# MAGIC **FE Bar stage: ML or Gen AI (make it intelligent) — part 2, ML.**
# MAGIC
# MAGIC Builds the **gold** customer feature table (joining billing trend, contract, and
# MAGIC the Gen-AI voice features), trains a **GradientBoosting** churn model tracked in
# MAGIC **MLflow**, scores every customer, and writes `gold.churn_scores`.
# MAGIC
# MAGIC Committed run evidence (from the local mirror, `evidence/model_metrics.json`):
# MAGIC **ROC-AUC 0.765 · precision@top-decile 0.677 (3.04× lift) · base rate 0.223.**
# MAGIC Top drivers: `churn_mentions` (0.30), `bill_trend_pct` (0.13), `n_retention_calls` (0.11).

# COMMAND ----------

# MAGIC %sql
# MAGIC -- GOLD feature table: one row per customer, billing + contract + VOICE features
# MAGIC CREATE OR REPLACE TABLE plenitude_febar.gold.customer_features AS
# MAGIC WITH bill AS (
# MAGIC   SELECT customer_id,
# MAGIC     avg(bill_amount_eur) AS avg_bill_eur,
# MAGIC     (avg(CASE WHEN month >= add_months(current_date(),-3) THEN bill_amount_eur END)
# MAGIC      - avg(CASE WHEN month <  add_months(current_date(),-3)
# MAGIC                 AND month >= add_months(current_date(),-6) THEN bill_amount_eur END))
# MAGIC      / nullif(avg(CASE WHEN month < add_months(current_date(),-3)
# MAGIC                 AND month >= add_months(current_date(),-6) THEN bill_amount_eur END),0)
# MAGIC      AS bill_trend_pct
# MAGIC   FROM plenitude_febar.silver.silver_consumption GROUP BY customer_id
# MAGIC ),
# MAGIC voice AS (
# MAGIC   SELECT customer_id,
# MAGIC     count(*) AS n_calls_90d,
# MAGIC     sum(CASE WHEN sentiment='negative' THEN 1 ELSE 0 END) AS n_negative_calls,
# MAGIC     sum(CASE WHEN intent='retention'  THEN 1 ELSE 0 END)  AS n_retention_calls,
# MAGIC     sum(CASE WHEN intent='billing'    THEN 1 ELSE 0 END)  AS n_billing_calls,
# MAGIC     avg(CASE sentiment WHEN 'negative' THEN -0.8 WHEN 'positive' THEN 0.7 ELSE 0.05 END) AS avg_sentiment,
# MAGIC     max(churn_signal) AS churn_mentions
# MAGIC   FROM plenitude_febar.silver.calls_enriched GROUP BY customer_id
# MAGIC )
# MAGIC SELECT c.*, coalesce(b.avg_bill_eur,c.monthly_bill_eur) AS avg_bill_eur,
# MAGIC   coalesce(b.bill_trend_pct,0) AS bill_trend_pct,
# MAGIC   coalesce(v.n_calls_90d,0) AS n_calls_90d, coalesce(v.n_negative_calls,0) AS n_negative_calls,
# MAGIC   coalesce(v.n_retention_calls,0) AS n_retention_calls, coalesce(v.n_billing_calls,0) AS n_billing_calls,
# MAGIC   coalesce(v.avg_sentiment,0.05) AS avg_sentiment, coalesce(v.churn_mentions,0) AS churn_mentions,
# MAGIC   datediff(c.contract_end_date, current_date()) AS days_to_contract_end,
# MAGIC   CASE WHEN datediff(c.contract_end_date, current_date())<90 THEN 1 ELSE 0 END AS contract_ending_soon,
# MAGIC   l.churned_next_90d
# MAGIC FROM plenitude_febar.silver.silver_customers c
# MAGIC LEFT JOIN bill  b USING (customer_id)
# MAGIC LEFT JOIN voice v USING (customer_id)
# MAGIC LEFT JOIN plenitude_febar.silver.silver_churn_labels l USING (customer_id);

# COMMAND ----------

import mlflow, mlflow.sklearn
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import roc_auc_score, average_precision_score

FEATURES = ["tenure_months","monthly_bill_eur","avg_bill_eur","bill_trend_pct","ebilling",
            "days_to_contract_end","contract_ending_soon","n_calls_90d","n_negative_calls",
            "n_retention_calls","n_billing_calls","avg_sentiment","churn_mentions",
            "is_variable","pay_risky","channel_comparator","is_dual"]

pdf = spark.table("plenitude_febar.gold.customer_features").toPandas()
pdf["is_variable"] = (pdf.contract_type == "variable").astype(int)
pdf["pay_risky"] = pdf.payment_method.isin(["postal","card"]).astype(int)
pdf["channel_comparator"] = (pdf.signup_channel == "comparator").astype(int)
pdf["is_dual"] = (pdf["product"] == "dual").astype(int)

X, y = pdf[FEATURES], pdf["churned_next_90d"]
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=7, stratify=y)

mlflow.set_experiment("/Shared/plenitude_febar_churn")
with mlflow.start_run(run_name="gbm_voice_churn") as run:
    clf = GradientBoostingClassifier(n_estimators=220, max_depth=3, learning_rate=0.06,
                                     subsample=0.9, random_state=7).fit(Xtr, ytr)
    p = clf.predict_proba(Xte)[:, 1]
    auc, ap = roc_auc_score(yte, p), average_precision_score(yte, p)
    k = int(len(p) * 0.10); topk = yte.iloc[np.argsort(-p)[:k]].mean()
    mlflow.log_metrics({"roc_auc": auc, "pr_auc": ap,
                        "precision_top_decile": topk, "lift": topk / yte.mean()})
    mlflow.sklearn.log_model(clf, "model",
        registered_model_name="plenitude_febar.gold.churn_model")
    print(f"ROC-AUC={auc:.3f}  PR-AUC={ap:.3f}  P@10%={topk:.3f}  lift={topk/yte.mean():.2f}x")

# COMMAND ----------

# score all customers -> gold.churn_scores
pdf["churn_probability"] = clf.predict_proba(X)[:, 1].round(4)
import pandas as pd
pdf["risk_band"] = pd.cut(pdf.churn_probability, [-.01,.25,.5,.75,1.01],
                          labels=["Low","Medium","High","Critical"]).astype(str)
(spark.createDataFrame(pdf[["customer_id","region","segment","product","monthly_bill_eur",
    "churn_probability","risk_band","n_negative_calls","n_retention_calls","churn_mentions"]])
   .write.mode("overwrite").saveAsTable("plenitude_febar.gold.churn_scores"))

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT risk_band, count(*) AS customers,
# MAGIC        round(avg(churn_probability),3) AS avg_prob,
# MAGIC        round(sum(monthly_bill_eur)*12,0) AS annual_revenue_eur
# MAGIC FROM plenitude_febar.gold.churn_scores
# MAGIC GROUP BY risk_band ORDER BY avg_prob DESC;

# COMMAND ----------

# MAGIC %md Next: **`04_lakebase_serving`** publishes scores to Lakebase for the app;
# MAGIC **`05_genie_room`** makes gold queryable in natural language.
