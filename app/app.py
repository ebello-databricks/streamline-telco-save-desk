"""
Streamline Telco — Save Desk (Databricks App)
==============================================
FE Bar stage: A Databricks App (surface it to the business).

Streamlit cockpit for retention agents and their manager:
  * KPI strip: at-risk subscribers, revenue at risk, saves logged today
  * Save list ranked by value at risk, filterable by region / driver / band
  * Subscriber card: why they may leave, next-best-offer, talk track
  * Log outcome -> written back to Lakebase `save_actions`

Data source, in order of preference:
  1. Lakebase (app resource `lakebase` injects PGHOST/PGUSER...)   — production
  2. committed parquet data/output/gold_save_list.parquet           — local dev
The click-through demo used in the role-play is the static twin: app/demo.html.

Deploy: databricks bundle deploy   (or: databricks apps deploy save-desk --source-code-path ./app)
Local:  streamlit run app/app.py
"""
from __future__ import annotations
import os
from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Streamline Telco · Save Desk", layout="wide")
LOCAL = Path(__file__).resolve().parents[1] / "data" / "output" / "gold_save_list.parquet"


def _pg():
    import psycopg
    from databricks.sdk import WorkspaceClient
    w = WorkspaceClient()   # app service principal credentials are injected
    return psycopg.connect(host=os.environ["PGHOST"], dbname=os.environ.get("PGDATABASE", "databricks_postgres"),
                           user=os.environ["PGUSER"], password=w.config.oauth_token().access_token,
                           sslmode="require")


@st.cache_data(ttl=300)
def load() -> pd.DataFrame:
    if os.environ.get("PGHOST"):
        with _pg() as c:
            return pd.read_sql("SELECT * FROM gold.save_list_synced", c)
    return pd.read_parquet(LOCAL)


def log_action(sub, agent, offer, outcome, notes):
    if os.environ.get("PGHOST"):
        with _pg() as c:
            c.execute("INSERT INTO save_desk.save_actions(subscriber_id,agent_id,offer,outcome,notes) VALUES (%s,%s,%s,%s,%s)",
                      (sub, agent, offer, outcome, notes))
    st.session_state.setdefault("actions", []).append((sub, offer, outcome))


df = load()
st.title("Save Desk")
st.caption("Who to call today, why they may leave, and what to offer · Streamline Telco (synthetic data)")

with st.sidebar:
    region = st.multiselect("Region", sorted(df.region.unique()))
    driver = st.multiselect("Driver", sorted(df.driver.unique()))
    bands = st.multiselect("Risk band", ["Critical", "High", "Medium", "Low"], default=["Critical", "High"])
v = df[df.risk_band.isin(bands)]
if region: v = v[v.region.isin(region)]
if driver: v = v[v.driver.isin(driver)]

c1, c2, c3, c4 = st.columns(4)
c1.metric("At-risk subscribers", f"{len(v):,}")
c2.metric("Annual revenue at risk", f"€{v.annual_value_eur.sum()/1e3:,.0f}k")
c3.metric("Expected loss if no action", f"€{v.value_at_risk_eur.sum()/1e3:,.0f}k")
c4.metric("Outcomes logged (session)", len(st.session_state.get("actions", [])))

st.dataframe(v[["subscriber_id", "region", "plan", "risk_band", "churn_probability", "value_at_risk_eur",
                "driver", "top_reasons", "next_best_offer"]].head(200), hide_index=True, use_container_width=True)

sid = st.selectbox("Open subscriber", v.subscriber_id.head(200))
if sid:
    r = v[v.subscriber_id == sid].iloc[0]
    a, b = st.columns([2, 1])
    a.subheader(f"{sid} · {r.plan} · {r.region}")
    a.write(f"**Churn probability:** {r.churn_probability:.0%} ({r.risk_band}) · **Value at risk:** €{r.value_at_risk_eur:,.0f}")
    a.write(f"**Why they may leave:** {r.top_reasons or 'n/a'}")
    track = r.get("talk_track")
    a.info(f"**Next best offer:** {r.next_best_offer}" + (f"\n\n{track}" if isinstance(track, str) and track else ""))
    with b.form("log"):
        outcome = st.radio("Outcome", ["accepted", "declined", "callback", "no_answer"])
        notes = st.text_input("Notes")
        if st.form_submit_button("Log outcome"):
            log_action(sid, os.environ.get("AGENT_ID", "AG017"), r.next_best_offer, outcome, notes)
            st.success("Saved to Lakebase · feeds next week's retraining")
