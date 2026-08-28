"""
FE Bar build — Plenitude "Voice-to-Retention" | Local pipeline runner
=====================================================================
Runs the SAME logic the Databricks notebooks run in the workspace, but
locally, so the repo can commit REAL execution evidence (readable as
text) as required by the FE Bar:

  1. SILVER  — clean + conform the raw landing tables
  2. GENAI   — enrich call transcripts with sentiment + intent + churn
               signal. In the workspace this is `ai_analyze_sentiment()` /
               `ai_classify()` (Foundation Model API). Locally we use a
               deterministic lexicon so the evidence is reproducible.
  3. FEATURES— build the customer-level feature table (GOLD)
  4. MODEL   — train + evaluate the churn model, score every customer
  5. WRITE   — churn_scores GOLD table + evidence files

Outputs (committed to the repo):
  data/output/gold_customer_features.parquet
  data/output/gold_churn_scores.parquet  (+ _sample.csv)
  data/output/call_enrichment.parquet    (+ _sample.csv)
  evidence/model_metrics.json
  evidence/model_run_output.txt
  evidence/query_results.md
"""
from __future__ import annotations
import json, io, datetime as dt
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import (roc_auc_score, average_precision_score,
                             precision_recall_fscore_support, confusion_matrix)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "output"
EV = ROOT / "evidence"; EV.mkdir(exist_ok=True)
REF_DATE = dt.date(2026, 6, 30)
_log = io.StringIO()


def log(m=""):
    print(m); _log.write(str(m) + "\n")


# ---------------------------------------------------------------------------
# 2. GEN AI ENRICHMENT — local, deterministic mirror of ai_analyze_sentiment
#    / ai_classify. Workspace notebook uses Foundation Model API instead.
# ---------------------------------------------------------------------------
NEG = ["arrabbiato", "assurdo", "sbagliata", "pessimo", "stanco", "disserviz",
       "troppo alto", "senza corrente", "non va bene", "reclamo"]
CHURN = ["cambio fornitore", "disdi", "concorrenza", "altro operatore", "enel",
         "passo alla", "non è più competitiv", "trovato di meglio"]
INTENTS = ["billing", "retention", "technical", "commercial", "self_service"]


def enrich_calls(calls: pd.DataFrame) -> pd.DataFrame:
    def score(t):
        tl = t.lower()
        neg = sum(w in tl for w in NEG)
        pos = ("soddisfatto" in tl) or ("gentiliss" in tl) or ("benissimo" in tl)
        churn = int(any(w in tl for w in CHURN))
        if neg >= 1 and not pos:
            sent, sc = "negative", round(-0.55 - 0.1 * neg, 2)
        elif pos:
            sent, sc = "positive", 0.7
        else:
            sent, sc = "neutral", 0.05
        return pd.Series({"sentiment": sent, "sentiment_score": sc,
                          "churn_signal": churn})
    enr = calls.join(calls.transcript.apply(score))
    # intent already carried in `queue` (what ai_classify would recover)
    enr["intent"] = enr["queue"]
    enr["complaint_flag"] = (enr.sentiment == "negative").astype(int)
    return enr[["call_id", "customer_id", "call_ts", "intent", "sentiment",
                "sentiment_score", "churn_signal", "complaint_flag", "duration_sec"]]


# ---------------------------------------------------------------------------
# 3. FEATURE TABLE (GOLD)
# ---------------------------------------------------------------------------
def build_features(cust, cons, contr, enr) -> pd.DataFrame:
    cons = cons.sort_values(["customer_id", "month"])
    g = cons.groupby("customer_id").bill_amount_eur
    last3 = g.apply(lambda s: s.tail(3).mean())
    prev3 = g.apply(lambda s: s.iloc[-6:-3].mean() if len(s) >= 6 else s.head(3).mean())
    bill_trend = ((last3 - prev3) / prev3.clip(lower=1)).rename("bill_trend_pct")
    avg_bill = g.mean().rename("avg_bill_eur")

    call = enr.groupby("customer_id").agg(
        n_calls_90d=("call_id", "count"),
        n_negative_calls=("complaint_flag", "sum"),
        n_retention_calls=("intent", lambda s: int((s == "retention").sum())),
        n_billing_calls=("intent", lambda s: int((s == "billing").sum())),
        avg_sentiment=("sentiment_score", "mean"),
        churn_mentions=("churn_signal", "max"),
    )
    f = cust.set_index("customer_id").join([bill_trend, avg_bill, call])
    f[["n_calls_90d", "n_negative_calls", "n_retention_calls", "n_billing_calls",
       "churn_mentions"]] = f[["n_calls_90d", "n_negative_calls", "n_retention_calls",
                               "n_billing_calls", "churn_mentions"]].fillna(0)
    f["avg_sentiment"] = f["avg_sentiment"].fillna(0.05)
    f["bill_trend_pct"] = f["bill_trend_pct"].fillna(0)
    end = pd.to_datetime(f["contract_end_date"]).dt.date
    f["days_to_contract_end"] = end.apply(lambda d: (d - REF_DATE).days)
    f["contract_ending_soon"] = (f["days_to_contract_end"] < 90).astype(int)
    return f.reset_index()


FEATURES = ["tenure_months", "monthly_bill_eur", "avg_bill_eur", "bill_trend_pct",
            "ebilling", "days_to_contract_end", "contract_ending_soon",
            "n_calls_90d", "n_negative_calls", "n_retention_calls", "n_billing_calls",
            "avg_sentiment", "churn_mentions",
            "is_variable", "pay_risky", "channel_comparator", "is_dual"]


def encode(f: pd.DataFrame) -> pd.DataFrame:
    f = f.copy()
    f["is_variable"] = (f.contract_type == "variable").astype(int)
    f["pay_risky"] = f.payment_method.isin(["postal", "card"]).astype(int)
    f["channel_comparator"] = (f.signup_channel == "comparator").astype(int)
    f["is_dual"] = (f["product"] == "dual").astype(int)
    return f


def main():
    log("=" * 70)
    log("PLENITUDE VOICE-TO-RETENTION  —  local pipeline run")
    log(f"run_ts={dt.datetime.now().isoformat(timespec='seconds')}  ref_date={REF_DATE}")
    log("=" * 70)

    cust = pd.read_parquet(OUT / "customers.parquet")
    cons = pd.read_parquet(OUT / "consumption.parquet")
    contr = pd.read_parquet(OUT / "contracts.parquet")
    calls = pd.read_parquet(OUT / "calls.parquet")
    churn = pd.read_parquet(OUT / "churn_labels.parquet")
    log(f"\n[silver] loaded raw: customers={len(cust):,}  consumption={len(cons):,}  "
        f"contracts={len(contr):,}  calls={len(calls):,}")

    # 2. enrichment
    enr = enrich_calls(calls)
    enr.to_parquet(OUT / "call_enrichment.parquet", index=False)
    enr.head(50).to_csv(OUT / "call_enrichment_sample.csv", index=False)
    sdist = enr.sentiment.value_counts(normalize=True).round(3).to_dict()
    log(f"[genai ] enriched {len(enr):,} calls  sentiment_mix={sdist}  "
        f"churn_signal_calls={int(enr.churn_signal.sum()):,}")

    # 3. features
    feats = build_features(cust, cons, contr, enr)
    feats = feats.merge(churn[["customer_id", "churned_next_90d"]], on="customer_id")
    feats = encode(feats)
    feats.to_parquet(OUT / "gold_customer_features.parquet", index=False)
    log(f"[gold  ] feature table: {len(feats):,} customers x {len(FEATURES)} features")

    # 4. model
    X, y = feats[FEATURES], feats["churned_next_90d"]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=7, stratify=y)
    clf = GradientBoostingClassifier(n_estimators=220, max_depth=3,
                                     learning_rate=0.06, subsample=0.9, random_state=7)
    clf.fit(Xtr, ytr)
    p_te = clf.predict_proba(Xte)[:, 1]
    auc = roc_auc_score(yte, p_te)
    ap = average_precision_score(yte, p_te)

    # precision/recall @ top-decile (the retention team's call list)
    k = int(len(p_te) * 0.10)
    idx = np.argsort(-p_te)[:k]
    topk_precision = yte.iloc[idx].mean()
    base_rate = yte.mean()
    lift = topk_precision / base_rate

    # operating point at 0.5
    yhat = (p_te >= 0.5).astype(int)
    pr, rc, f1, _ = precision_recall_fscore_support(yte, yhat, average="binary", zero_division=0)
    cm = confusion_matrix(yte, yhat).tolist()

    log("\n[model ] GradientBoosting  (test set n={:,})".format(len(yte)))
    log(f"         ROC-AUC            = {auc:.3f}")
    log(f"         PR-AUC (avg prec)  = {ap:.3f}")
    log(f"         base churn rate    = {base_rate:.3f}")
    log(f"         precision @ top10% = {topk_precision:.3f}   (lift {lift:.2f}x over base)")
    log(f"         precision @0.5     = {pr:.3f}   recall = {rc:.3f}   f1 = {f1:.3f}")
    log(f"         confusion matrix   = {cm}   [[TN,FP],[FN,TP]]")

    imp = sorted(zip(FEATURES, clf.feature_importances_), key=lambda x: -x[1])
    log("\n[model ] top feature importances:")
    for name, v in imp[:8]:
        log(f"         {name:<22} {v:6.3f}  " + "#" * int(v * 80))

    # 5. score everyone -> GOLD churn_scores
    feats["churn_probability"] = clf.predict_proba(X)[:, 1].round(4)
    bands = pd.cut(feats.churn_probability, [-0.01, 0.25, 0.5, 0.75, 1.01],
                   labels=["Low", "Medium", "High", "Critical"])
    feats["risk_band"] = bands.astype(str)

    def reasons(r):
        out = []
        if r.n_retention_calls > 0: out.append("called retention line")
        if r.churn_mentions > 0: out.append("mentioned switching/competitor")
        if r.bill_trend_pct > 0.10: out.append(f"bill up {r.bill_trend_pct*100:.0f}%")
        if r.n_negative_calls > 0: out.append(f"{int(r.n_negative_calls)} negative call(s)")
        if r.contract_ending_soon: out.append("contract ends <90d")
        if r.is_variable: out.append("variable tariff")
        return "; ".join(out[:3]) or "stable profile"
    feats["top_reasons"] = feats.apply(reasons, axis=1)

    scores = feats[["customer_id", "region", "segment", "product", "monthly_bill_eur",
                    "churn_probability", "risk_band", "top_reasons",
                    "n_negative_calls", "n_retention_calls", "churn_mentions"]]
    scores = scores.sort_values("churn_probability", ascending=False)
    scores.to_parquet(OUT / "gold_churn_scores.parquet", index=False)
    scores.head(50).to_csv(OUT / "gold_churn_scores_sample.csv", index=False)

    band_ct = feats.risk_band.value_counts().reindex(["Critical", "High", "Medium", "Low"])
    log("\n[gold  ] churn_scores risk bands:")
    for b, n in band_ct.items():
        log(f"         {b:<9} {int(n):>6,}  ({n/len(feats)*100:4.1f}%)")

    # ----- evidence files -----
    metrics = dict(
        run_ts=dt.datetime.now().isoformat(timespec="seconds"),
        model="GradientBoostingClassifier(n_estimators=220,max_depth=3,lr=0.06)",
        n_customers=int(len(feats)), n_features=len(FEATURES),
        test_n=int(len(yte)), roc_auc=round(float(auc), 4),
        pr_auc=round(float(ap), 4), base_churn_rate=round(float(base_rate), 4),
        precision_at_top_decile=round(float(topk_precision), 4),
        lift_over_base=round(float(lift), 3),
        precision_at_0_5=round(float(pr), 4), recall_at_0_5=round(float(rc), 4),
        f1_at_0_5=round(float(f1), 4), confusion_matrix=cm,
        top_features=[{"feature": n, "importance": round(float(v), 4)} for n, v in imp[:10]],
        risk_bands={str(b): int(n) for b, n in band_ct.items()},
    )
    (EV / "model_metrics.json").write_text(json.dumps(metrics, indent=2))

    # query_results.md — the kind of SQL the Genie room / dashboard runs
    q = ["# Query results (GOLD layer) — committed run evidence\n",
         "> Produced by `data/run_local_pipeline.py`. In the workspace these are "
         "Databricks SQL / Genie answers over the same gold tables.\n",
         "## Q1 — Customers by risk band\n```",
         band_ct.rename("customers").to_frame().to_string(), "```\n",
         "## Q2 — Top 10 at-risk customers (retention call list)\n```",
         scores.head(10).to_string(index=False), "```\n",
         "## Q3 — Churn rate by region (highest first)\n```",
         (feats.groupby("region").churned_next_90d.mean().mul(100).round(1)
          .sort_values(ascending=False).rename("churn_rate_%").to_frame().to_string()), "```\n",
         "## Q4 — Avg churn probability by contract type & payment method\n```",
         (feats.pivot_table(index="contract_type", columns="pay_risky",
                            values="churn_probability", aggfunc="mean").round(3).to_string()), "```\n",
         "## Q5 — Value at risk in the Critical + High bands\n```"]
    at_risk = feats[feats.risk_band.isin(["Critical", "High"])]
    var_annual = (at_risk.monthly_bill_eur.sum() * 12)
    q += [f"customers at risk (Critical+High): {len(at_risk):,}",
          f"annual revenue represented        : EUR {var_annual:,.0f}",
          f"(gross-margin @ 22% ≈ EUR {var_annual*0.22:,.0f} of margin exposed)", "```\n"]
    (EV / "query_results.md").write_text("\n".join(q))

    (EV / "model_run_output.txt").write_text(_log.getvalue())
    log("\n[done  ] wrote gold tables + evidence/{model_metrics.json,model_run_output.txt,query_results.md}")


if __name__ == "__main__":
    main()
