"""
FE Bar build — Streamline Telco "Save Desk" | Local pipeline runner
====================================================================
Runs the SAME logic as the Databricks notebooks, locally, so the repo
commits REAL execution evidence (readable as text):

  1. SILVER   — clean + conform the raw landing tables (Lakeflow expectations)
  2. GEN AI   — enrich care-call transcripts: sentiment, intent, switch intent.
                Workspace = ai_analyze_sentiment / ai_classify / ai_query.
                Locally = deterministic lexicon mirror (reproducible evidence).
  3. FEATURES — subscriber-level feature table (GOLD)
  4. ML       — train + evaluate churn model, score every subscriber
  5. ACTION   — next-best-offer + agent talk track per at-risk subscriber
  6. SERVE    — load save list into an OLTP store + write back an agent outcome
                (workspace = Lakebase Postgres; locally = SQLite stand-in)
  7. GENIE    — the business questions the Genie agent answers, run as SQL
  8. APP      — export the demo app dataset (app/demo_data.js)
"""
from __future__ import annotations
import json, io, sqlite3, time, datetime as dt
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
REF_DATE = dt.date(2026, 9, 30)
_log = io.StringIO()


def log(m=""):
    print(m); _log.write(str(m) + "\n")


# ---------------------------------------------------------------------------
# 1. SILVER — same contracts as the Lakeflow expectations in 01_ingest_lakeflow.py
# ---------------------------------------------------------------------------
def to_silver(subs, contr, usage, calls):
    before = dict(subscribers=len(subs), contracts=len(contr), usage=len(usage), care_calls=len(calls))
    subs = subs.dropna(subset=["subscriber_id"]).drop_duplicates("subscriber_id")
    contr = contr[contr.monthly_price_eur > 0]
    usage = usage[(usage.bill_amount_eur > 0) & (usage.bill_amount_eur < 1000) & (usage.dropped_calls >= 0)]
    calls = calls[calls.transcript.str.len() > 0]
    after = dict(subscribers=len(subs), contracts=len(contr), usage=len(usage), care_calls=len(calls))
    return subs, contr, usage, calls, before, after


# ---------------------------------------------------------------------------
# 2. GEN AI ENRICHMENT — local mirror of ai_analyze_sentiment / ai_classify / ai_query
# ---------------------------------------------------------------------------
NEG = ["ridiculous", "annoyed", "unacceptable", "terrible", "disappointed", "cannot keep",
       "nothing changes", "so slow", "goes down", "faulty", "i am leaving", "not competitive"]
POS = ["very happy", "very satisfied", "really helpful"]
SWITCH = ["other operator", "porting", "pac code", "switching provider", "other providers",
          "better deal", "i am leaving", "cancel"]
INTENT_KW = {"network": ["signal", "data", "fibre", "drop", "outage"],
             "billing": ["bill", "invoice", "charge", "debit", "roaming"],
             "retention": ["contract ends", "renew", "cancel", "porting", "pac code", "switch"],
             "device": ["phone", "handset", "esim", "repair"]}


def enrich_calls(calls: pd.DataFrame) -> pd.DataFrame:
    def score(t):
        tl = t.lower()
        n = sum(w in tl for w in NEG); pos = any(w in tl for w in POS)
        sent, sc = ("negative", round(-0.5 - 0.1 * n, 2)) if n and not pos else \
                   ("positive", 0.7) if pos else ("neutral", 0.05)
        intent = next((k for k in ["retention", "network", "billing", "device"]
                       if any(w in tl for w in INTENT_KW[k])), "general")
        return pd.Series({"sentiment": sent, "sentiment_score": sc, "intent": intent,
                          "switch_intent": int(any(w in tl for w in SWITCH))})
    enr = calls.join(calls.transcript.apply(score))
    acc = (enr.intent == enr.queue).mean()
    return enr[["call_id", "subscriber_id", "call_ts", "intent", "sentiment",
                "sentiment_score", "switch_intent", "duration_sec", "transcript"]], acc


# ---------------------------------------------------------------------------
# 3. FEATURE TABLE (GOLD)
# ---------------------------------------------------------------------------
def build_features(subs, contr, usage, enr, ref_date=REF_DATE) -> pd.DataFrame:
    u = usage.sort_values(["subscriber_id", "month"])
    last2 = u.groupby("subscriber_id").tail(2).groupby("subscriber_id")
    first4 = u.groupby("subscriber_id").head(4).groupby("subscriber_id")
    net = pd.DataFrame({
        "dropped_calls_l2m": last2.dropped_calls.mean(),
        "dl_speed_l2m": last2.avg_dl_speed_mbps.mean(),
        "bill_trend_pct": (last2.bill_amount_eur.mean() - first4.bill_amount_eur.mean()) / first4.bill_amount_eur.mean(),
        "avg_bill_eur": u.groupby("subscriber_id").bill_amount_eur.mean(),
    })
    call = enr.groupby("subscriber_id").agg(
        n_calls_60d=("call_id", "count"),
        n_negative_calls=("sentiment", lambda s: int((s == "negative").sum())),
        n_network_calls=("intent", lambda s: int((s == "network").sum())),
        n_billing_calls=("intent", lambda s: int((s == "billing").sum())),
        n_retention_calls=("intent", lambda s: int((s == "retention").sum())),
        avg_sentiment=("sentiment_score", "mean"),
        switch_intent=("switch_intent", "max"),
    )
    f = (subs.set_index("subscriber_id")
         .join(contr.set_index("subscriber_id")[["monthly_price_eur", "handset_financed", "commitment_end_date"]])
         .join(net).join(call))
    cc = ["n_calls_60d", "n_negative_calls", "n_network_calls", "n_billing_calls", "n_retention_calls", "switch_intent"]
    f[cc] = f[cc].fillna(0).astype(int)
    f["avg_sentiment"] = f["avg_sentiment"].fillna(0.05)
    f["days_to_commitment_end"] = pd.to_datetime(f.commitment_end_date).dt.date.apply(lambda d: (d - ref_date).days)
    f["out_of_contract"] = (f.days_to_commitment_end < 0).astype(int)
    f["commitment_ends_60d"] = f.days_to_commitment_end.between(0, 59).astype(int)
    f["from_comparison_site"] = (f.acquisition_channel == "comparison_site").astype(int)
    f["pays_by_card"] = (f.payment_method == "card").astype(int)
    f["multi_line"] = (f.lines > 1).astype(int)
    return f.reset_index()


FEATURES = ["tenure_months", "lines", "monthly_price_eur", "handset_financed", "avg_bill_eur",
            "bill_trend_pct", "dropped_calls_l2m", "dl_speed_l2m", "days_to_commitment_end",
            "out_of_contract", "commitment_ends_60d", "from_comparison_site", "pays_by_card",
            "multi_line", "n_calls_60d", "n_negative_calls", "n_network_calls",
            "n_billing_calls", "n_retention_calls", "avg_sentiment", "switch_intent"]


# ---------------------------------------------------------------------------
# 5. NEXT-BEST-OFFER + TALK TRACK (workspace: ai_query writes the talk track)
# ---------------------------------------------------------------------------
OFFERS = {
    "network":  ("Network fix + 1 month credit", 15.0),
    "price":    ("Loyalty price match (-20% for 12 months)", 60.0),
    "contract": ("Early renewal with handset upgrade", 45.0),
    "service":  ("Priority care callback + bill credit", 10.0),
}


def primary_driver(r):
    hard_net = r.dropped_calls_l2m > 3.5 or r.dl_speed_l2m < 15
    hard_price = r.bill_trend_pct > 0.15
    if hard_price and (not hard_net or r.bill_trend_pct > 0.35): return "price"
    if hard_net: return "network"
    if r.commitment_ends_60d or r.out_of_contract or r.n_retention_calls > 0: return "contract"
    if r.n_network_calls > 0: return "network"
    if r.n_billing_calls > 0: return "price"
    return "service"


def reasons(r):
    out = []
    if r.switch_intent: out.append("mentioned switching / porting on a care call")
    if r.dropped_calls_l2m > 3.5: out.append(f"{r.dropped_calls_l2m:.0f} dropped calls / month")
    if r.dl_speed_l2m < 15: out.append(f"data speed down to {r.dl_speed_l2m:.0f} Mbps")
    if r.bill_trend_pct > 0.15: out.append(f"bill up {r.bill_trend_pct*100:.0f}%")
    if r.commitment_ends_60d: out.append(f"commitment ends in {r.days_to_commitment_end} days")
    if r.out_of_contract: out.append("out of contract")
    if r.n_network_calls and not (r.dropped_calls_l2m > 3.5 or r.dl_speed_l2m < 15):
        out.append(f"{r.n_network_calls} care call(s) about network quality")
    if r.n_retention_calls: out.append(f"{r.n_retention_calls} call(s) to the retention line")
    if r.n_negative_calls: out.append(f"{r.n_negative_calls} negative care call(s)")
    if r.tenure_months < 12: out.append(f"only {r.tenure_months} months with us")
    if r.from_comparison_site: out.append("joined via a price-comparison site")
    if r.pays_by_card: out.append("pays by card, not direct debit")
    return out[:3] or ["several weaker signals combined: review before calling"]


def talk_track(r, offer):
    lead = {"network": "I can see you have had connection problems recently, and I am sorry about that.",
            "price": "I noticed your last bills were higher than usual, so I wanted to review your plan with you.",
            "contract": "Your commitment period is ending soon, and as a loyal customer I have a renewal offer for you.",
            "service": "I wanted to check you are getting the most from your Streamline plan."}[r.driver]
    close = {"network": "Confirm the engineer visit date and book a follow-up call in 7 days.",
             "price": "Confirm the new monthly price in writing before ending the call.",
             "contract": "Send the renewal summary by SMS while on the call.",
             "service": "Book a follow-up call in 7 days."}[r.driver]
    return f"{lead} I would like to offer you: {offer.lower()}. {close}"


def main():
    t0 = time.time()
    log("=" * 72)
    log("STREAMLINE TELCO SAVE DESK  —  local pipeline run (synthetic data)")
    log(f"run_ts={dt.datetime.now().isoformat(timespec='seconds')}  ref_date={REF_DATE}")
    log("=" * 72)

    subs = pd.read_parquet(OUT / "subscribers.parquet")
    contr = pd.read_parquet(OUT / "contracts.parquet")
    usage = pd.read_parquet(OUT / "usage.parquet")
    calls = pd.read_parquet(OUT / "care_calls.parquet")
    churn = pd.read_parquet(OUT / "churn_labels.parquet")

    subs, contr, usage, calls, before, after = to_silver(subs, contr, usage, calls)
    log("\n[1 silver ] expectations applied (rows before -> after):")
    for k in before: log(f"            {k:<12} {before[k]:>8,} -> {after[k]:>8,}")

    enr, intent_acc = enrich_calls(calls)
    enr.drop(columns="transcript").to_parquet(OUT / "call_enrichment.parquet", index=False)
    enr.head(50).to_csv(OUT / "call_enrichment_sample.csv", index=False)
    log(f"\n[2 gen ai ] enriched {len(enr):,} care calls")
    log(f"            sentiment mix   = {enr.sentiment.value_counts(normalize=True).round(3).to_dict()}")
    log(f"            intent mix      = {enr.intent.value_counts().to_dict()}")
    log(f"            switch-intent calls = {int(enr.switch_intent.sum()):,}")
    log(f"            intent agreement vs. IVR queue label = {intent_acc:.1%}")

    feats = build_features(subs, contr, usage, enr).merge(
        churn[["subscriber_id", "churned_next_60d"]], on="subscriber_id")
    feats.to_parquet(OUT / "gold_subscriber_features.parquet", index=False)
    log(f"\n[3 gold   ] feature table: {len(feats):,} subscribers x {len(FEATURES)} features")

    X, y = feats[FEATURES], feats["churned_next_60d"]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=7, stratify=y)
    clf = GradientBoostingClassifier(n_estimators=250, max_depth=3, learning_rate=0.06,
                                     subsample=0.9, random_state=7).fit(Xtr, ytr)
    p = clf.predict_proba(Xte)[:, 1]
    auc, ap = roc_auc_score(yte, p), average_precision_score(yte, p)
    k = int(len(p) * 0.10); idx = np.argsort(-p)[:k]
    top_prec, base = yte.iloc[idx].mean(), yte.mean()
    top_recall = yte.iloc[idx].sum() / yte.sum()
    yhat = (p >= 0.5).astype(int)
    pr, rc, f1, _ = precision_recall_fscore_support(yte, yhat, average="binary", zero_division=0)
    cm = confusion_matrix(yte, yhat).tolist()

    # Ablation: same model WITHOUT the Gen AI call features -> value of the voice signal
    voice = ["n_calls_60d", "n_negative_calls", "n_network_calls", "n_billing_calls",
             "n_retention_calls", "avg_sentiment", "switch_intent"]
    nv = [c for c in FEATURES if c not in voice]
    clf_nv = GradientBoostingClassifier(n_estimators=250, max_depth=3, learning_rate=0.06,
                                        subsample=0.9, random_state=7).fit(Xtr[nv], ytr)
    p_nv = clf_nv.predict_proba(Xte[nv])[:, 1]
    auc_nv = roc_auc_score(yte, p_nv)
    top_prec_nv = yte.iloc[np.argsort(-p_nv)[:k]].mean()

    log(f"\n[4 ml     ] GradientBoostingClassifier  (train n={len(ytr):,}, test n={len(yte):,})")
    log(f"            ROC-AUC              = {auc:.3f}")
    log(f"            PR-AUC               = {ap:.3f}")
    log(f"            base churn rate      = {base:.3f}")
    log(f"            precision @ top 10%  = {top_prec:.3f}   (lift {top_prec/base:.2f}x)")
    log(f"            recall    @ top 10%  = {top_recall:.3f}   (share of all churners caught)")
    log(f"            precision/recall@0.5 = {pr:.3f} / {rc:.3f}   f1 = {f1:.3f}")
    log(f"            confusion matrix     = {cm}   [[TN,FP],[FN,TP]]")
    log(f"            ablation WITHOUT Gen AI call features: ROC-AUC {auc_nv:.3f}, "
        f"precision@top10% {top_prec_nv:.3f}  -> Gen AI adds +{(auc-auc_nv):.3f} AUC")
    imp = sorted(zip(FEATURES, clf.feature_importances_), key=lambda x: -x[1])
    log("            top feature importances:")
    for n_, v in imp[:8]:
        log(f"              {n_:<24} {v:6.3f}  " + "#" * int(v * 80))

    # score everyone
    feats["churn_probability"] = clf.predict_proba(X)[:, 1].round(4)
    feats["risk_band"] = pd.cut(feats.churn_probability, [-0.01, 0.2, 0.4, 0.6, 1.01],
                                labels=["Low", "Medium", "High", "Critical"]).astype(str)
    feats["driver"] = feats.apply(primary_driver, axis=1)
    feats["next_best_offer"] = feats.driver.map(lambda d: OFFERS[d][0])
    feats["offer_cost_eur"] = feats.driver.map(lambda d: OFFERS[d][1])
    feats["annual_value_eur"] = (feats.avg_bill_eur * 12).round(0)
    feats["value_at_risk_eur"] = (feats.annual_value_eur * feats.churn_probability).round(0)
    feats["top_reasons"] = feats.apply(lambda r: "; ".join(reasons(r)), axis=1)
    feats["talk_track"] = feats.apply(lambda r: talk_track(r, r.next_best_offer), axis=1)

    cols = ["subscriber_id", "region", "segment", "plan", "lines", "tenure_months", "avg_bill_eur",
            "annual_value_eur", "churn_probability", "risk_band", "value_at_risk_eur", "driver",
            "top_reasons", "next_best_offer", "offer_cost_eur", "talk_track",
            "dropped_calls_l2m", "dl_speed_l2m", "bill_trend_pct", "days_to_commitment_end", "switch_intent"]
    scores = feats[cols].sort_values("value_at_risk_eur", ascending=False)
    scores.to_parquet(OUT / "gold_save_list.parquet", index=False)
    scores.head(50).to_csv(OUT / "gold_save_list_sample.csv", index=False)
    bands = feats.risk_band.value_counts().reindex(["Critical", "High", "Medium", "Low"]).fillna(0).astype(int)
    log("\n[5 action ] save list scored + next-best-offer assigned:")
    for b, n_ in bands.items(): log(f"            {b:<9} {n_:>6,}  ({n_/len(feats)*100:4.1f}%)")
    log(f"            driver mix (High+Critical) = "
        f"{feats[feats.risk_band.isin(['High','Critical'])].driver.value_counts().to_dict()}")

    # 6. SERVE — OLTP stand-in for Lakebase: point lookup + agent write-back
    db = OUT / "lakebase_standin.sqlite"; db.unlink(missing_ok=True)
    con = sqlite3.connect(db)
    scores.to_sql("save_list", con, index=False)
    con.execute("CREATE UNIQUE INDEX ix_sub ON save_list(subscriber_id)")
    con.execute("""CREATE TABLE save_actions(action_id INTEGER PRIMARY KEY AUTOINCREMENT,
                   subscriber_id TEXT, agent_id TEXT, offer TEXT, outcome TEXT, ts TEXT)""")
    top = scores.iloc[0]
    t = time.perf_counter()
    for sid in scores.subscriber_id.sample(500, random_state=1):
        con.execute("SELECT churn_probability, next_best_offer FROM save_list WHERE subscriber_id=?", (sid,)).fetchone()
    lat_ms = (time.perf_counter() - t) / 500 * 1000
    con.execute("INSERT INTO save_actions(subscriber_id,agent_id,offer,outcome,ts) VALUES (?,?,?,?,?)",
                (top.subscriber_id, "AG017", top.next_best_offer, "accepted", dt.datetime.now().isoformat(timespec="seconds")))
    con.commit()
    wb = con.execute("SELECT * FROM save_actions").fetchall()
    log(f"\n[6 serve  ] OLTP serving (SQLite stand-in for Lakebase Postgres): {len(scores):,} rows loaded")
    log(f"            500 point lookups by subscriber_id: avg {lat_ms:.3f} ms")
    log(f"            agent write-back -> save_actions: {wb}")
    con.close(); db.unlink()

    # 7. GENIE — business questions answered as SQL over gold
    hc = feats[feats.risk_band.isin(["High", "Critical"])]
    genie = [
        ("How many subscribers are High or Critical risk, and how much annual revenue do they represent?",
         "SELECT risk_band, COUNT(*) subs, SUM(annual_value_eur) revenue FROM gold.save_list WHERE risk_band IN ('High','Critical') GROUP BY risk_band",
         hc.groupby("risk_band").agg(subs=("subscriber_id", "count"), revenue_eur=("annual_value_eur", "sum")).to_string()),
        ("Which region has the most at-risk subscribers because of network problems?",
         "SELECT region, COUNT(*) FROM gold.save_list WHERE risk_band IN ('High','Critical') AND driver='network' GROUP BY region ORDER BY 2 DESC",
         hc[hc.driver == "network"].region.value_counts().rename("at_risk_network").to_frame().to_string()),
        ("Show the 10 subscribers with the highest value at risk and what we should offer them.",
         "SELECT subscriber_id, plan, churn_probability, value_at_risk_eur, next_best_offer FROM gold.save_list ORDER BY value_at_risk_eur DESC LIMIT 10",
         scores.head(10)[["subscriber_id", "plan", "churn_probability", "value_at_risk_eur", "next_best_offer"]].to_string(index=False)),
        ("What is the actual churn rate for customers who mentioned switching on a care call vs. those who did not?",
         "SELECT switch_intent, AVG(churned_next_60d) FROM gold.subscriber_features GROUP BY switch_intent",
         feats.groupby("switch_intent").churned_next_60d.mean().mul(100).round(1).rename("churn_rate_%").to_frame().to_string()),
        ("Churn rate by plan",
         "SELECT plan, AVG(churned_next_60d)*100 FROM gold.subscriber_features GROUP BY plan ORDER BY 2 DESC",
         feats.groupby("plan").churned_next_60d.mean().mul(100).round(1).sort_values(ascending=False).rename("churn_rate_%").to_frame().to_string()),
    ]
    md = ["# Genie agent questions — answered over the GOLD layer (run evidence)\n",
          "> Produced by `data/run_local_pipeline.py` on synthetic data. In the workspace the Genie agent "
          "generates equivalent SQL over `streamline_telco.gold.*` (see `genie/genie_space_config.json`).\n"]
    for i, (qq, sql, ans) in enumerate(genie, 1):
        md += [f"## Q{i} — {qq}\n", f"```sql\n{sql}\n```\n", f"```\n{ans}\n```\n"]
    (EV / "query_results.md").write_text("\n".join(md))
    log(f"\n[7 genie  ] answered {len(genie)} business questions -> evidence/query_results.md")

    # 8. APP dataset — top 300 by value at risk for the HTML cockpit
    demo = scores.head(300).copy()
    demo["bill_trend_pct"] = demo.bill_trend_pct.round(3); demo["dl_speed_l2m"] = demo.dl_speed_l2m.round(1)
    summary = dict(n_subs=int(len(feats)), bands={k: int(v) for k, v in bands.items()},
                   hc_subs=int(len(hc)), hc_revenue=float(hc.annual_value_eur.sum()),
                   hc_value_at_risk=float(hc.value_at_risk_eur.sum()), roc_auc=round(float(auc), 3),
                   lift=round(float(top_prec / base), 2), top_prec=round(float(top_prec), 3),
                   driver_mix={k: int(v) for k, v in hc.driver.value_counts().items()},
                   region_mix={k: int(v) for k, v in hc.region.value_counts().items()})
    (ROOT / "app" / "demo_data.js").write_text(
        "// generated by data/run_local_pipeline.py — top 300 of gold.save_list (synthetic)\n"
        f"window.SUMMARY = {json.dumps(summary)};\nwindow.SAVE_LIST = {demo.to_json(orient='records')};\n")
    log(f"[8 app    ] exported top 300 save-list rows -> app/demo_data.js")

    metrics = dict(run_ts=dt.datetime.now().isoformat(timespec="seconds"),
                   model="GradientBoostingClassifier(n_estimators=250,max_depth=3,lr=0.06)",
                   n_subscribers=int(len(feats)), n_features=len(FEATURES), test_n=int(len(yte)),
                   roc_auc=round(float(auc), 4), pr_auc=round(float(ap), 4),
                   base_churn_rate_60d=round(float(base), 4),
                   precision_at_top_decile=round(float(top_prec), 4),
                   recall_at_top_decile=round(float(top_recall), 4),
                   lift_at_top_decile=round(float(top_prec / base), 3),
                   precision_at_0_5=round(float(pr), 4), recall_at_0_5=round(float(rc), 4),
                   confusion_matrix=cm,
                   ablation_without_genai=dict(roc_auc=round(float(auc_nv), 4),
                                               precision_at_top_decile=round(float(top_prec_nv), 4)),
                   top_features=[{"feature": a, "importance": round(float(b), 4)} for a, b in imp[:10]],
                   risk_bands={k: int(v) for k, v in bands.items()},
                   genai_intent_agreement=round(float(intent_acc), 4))
    (EV / "model_metrics.json").write_text(json.dumps(metrics, indent=2))
    log(f"\n[done     ] {time.time()-t0:.1f}s — evidence/{{model_metrics.json,model_run_output.txt,query_results.md}}")
    (EV / "model_run_output.txt").write_text(_log.getvalue())


if __name__ == "__main__":
    main()
