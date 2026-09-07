"""
Plenitude — Voice-to-Retention | Retention Cockpit (Databricks App)
===================================================================
FE Bar stage: A Databricks App (surface it to the business).

A Streamlit cockpit for the retention team. It reads the ranked churn call
list from the GOLD layer (served via Lakebase in production; falls back to the
committed parquet locally so the app runs anywhere), lets an agent filter by
region / risk band / "mentioned switching", shows each customer's top churn
reasons, and logs a retention action back to Lakebase.

Deploy: `databricks apps deploy plenitude-retention --source-code-path ./app`
Run locally: `streamlit run app/app.py`
"""
from __future__ import annotations
import os
from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Plenitude · Voice-to-Retention", page_icon="⚡", layout="wide")

BAND_COLOR = {"Critical": "#E5391D", "High": "#A9640A", "Medium": "#3C5A63", "Low": "#00875A"}
MARGIN = 0.22  # gross-margin assumption for value-at-risk

# Data source, in order of preference:
#   1. Lakebase (PGHOST set)         — operational serving, Tier 2
#   2. Unity Catalog via SQL warehouse (DATABRICKS_WAREHOUSE_ID set) — the deployed default
#   3. committed parquet             — local dev fallback so the app runs anywhere
GOLD_SCORES = os.environ.get("GOLD_SCORES_TABLE", "plenitude_febar.gold.churn_scores")
ACTIONS_TABLE = os.environ.get("ACTIONS_TABLE", "plenitude_febar.gold.retention_actions")
WAREHOUSE_ID = os.environ.get("DATABRICKS_WAREHOUSE_ID")


def _uc_conn():
    """Databricks SQL connection, authenticated as the app's service principal."""
    from databricks import sql as dbsql
    from databricks.sdk.core import Config
    cfg = Config()  # picks up the app's injected credentials (or local CLI profile)
    return dbsql.connect(
        server_hostname=cfg.host.replace("https://", "").rstrip("/"),
        http_path=f"/sql/1.0/warehouses/{WAREHOUSE_ID}",
        credentials_provider=lambda: cfg.authenticate)


def _pg_conn():
    import psycopg2
    return psycopg2.connect(
        host=os.environ["PGHOST"], dbname="databricks_postgres",
        user=os.environ["PGUSER"], password=os.environ["PGPASSWORD"], sslmode="require")


@st.cache_data(ttl=300)
def load_scores() -> pd.DataFrame:
    if os.environ.get("PGHOST"):
        with _pg_conn() as conn:
            return pd.read_sql("SELECT * FROM churn_scores_synced", conn)
    if WAREHOUSE_ID:
        with _uc_conn() as conn:
            return pd.read_sql(f"SELECT * FROM {GOLD_SCORES}", conn)
    p = Path(__file__).resolve().parents[1] / "data" / "output" / "gold_churn_scores.parquet"
    return pd.read_parquet(p)


def log_action(customer_id, agent, action, offer, notes):
    if os.environ.get("PGHOST"):
        conn = _pg_conn()
        cur = conn.cursor()
        cur.execute("INSERT INTO retention_actions (customer_id,agent,action,offer_eur,notes)"
                    " VALUES (%s,%s,%s,%s,%s)", (customer_id, agent, action, offer, notes))
        conn.commit()
    elif WAREHOUSE_ID:
        with _uc_conn() as conn:
            cur = conn.cursor()
            cur.execute(f"CREATE TABLE IF NOT EXISTS {ACTIONS_TABLE} "
                        "(customer_id STRING, agent STRING, action STRING, offer_eur INT, "
                        "notes STRING, logged_at TIMESTAMP)")
            cur.execute(f"INSERT INTO {ACTIONS_TABLE} "
                        "(customer_id,agent,action,offer_eur,notes,logged_at) "
                        "VALUES (?,?,?,?,?, current_timestamp())",
                        [customer_id, agent, action, int(offer), notes])
    st.session_state.setdefault("logged", []).append((customer_id, action, offer))


df = load_scores()

st.title("⚡ Voice-to-Retention — Retention Cockpit")
st.caption("Plenitude B2C energy · churn scored from contact-centre voice + billing signals · **synthetic data**")

# ---- KPI row (baseline -> after framing) ----
at_risk = df[df.risk_band.isin(["Critical", "High"])]
var = at_risk.monthly_bill_eur.sum() * 12
c1, c2, c3, c4 = st.columns(4)
c1.metric("Customers scored", f"{len(df):,}")
c2.metric("At-risk (High+Critical)", f"{len(at_risk):,}", f"{len(at_risk)/len(df)*100:.1f}% of base")
c3.metric("Annual revenue at risk", f"€{var:,.0f}")
c4.metric("Margin exposed (≈22%)", f"€{var*MARGIN:,.0f}")

# ---- filters ----
with st.sidebar:
    st.header("Call list filters")
    bands = st.multiselect("Risk band", ["Critical", "High", "Medium", "Low"],
                           default=["Critical", "High"])
    regions = st.multiselect("Region", sorted(df.region.unique()))
    only_switch = st.checkbox("Only customers who mentioned switching", value=False)
    topn = st.slider("Show top N", 10, 200, 50, step=10)

view = df[df.risk_band.isin(bands)]
if regions:
    view = view[view.region.isin(regions)]
if only_switch:
    view = view[view.churn_mentions == 1]
view = view.sort_values("churn_probability", ascending=False).head(topn)

st.subheader(f"📞 Prioritised retention call list — {len(view)} customers")
show = view.copy()
show["churn_%"] = (show.churn_probability * 100).round(1)
show["value/yr €"] = (show.monthly_bill_eur * 12).round(0)
st.dataframe(
    show[["customer_id", "region", "segment", "product", "risk_band",
          "churn_%", "value/yr €", "n_negative_calls", "n_retention_calls",
          "churn_mentions", "top_reasons"]] if "top_reasons" in show.columns else
    show[["customer_id", "region", "segment", "product", "risk_band",
          "churn_%", "value/yr €", "n_negative_calls", "n_retention_calls", "churn_mentions"]],
    use_container_width=True, hide_index=True)

# ---- action logging ----
st.subheader("✅ Log a retention action")
with st.form("action"):
    a, b, c = st.columns(3)
    cust = a.selectbox("Customer", view.customer_id.tolist() if len(view) else df.customer_id.head(20).tolist())
    action = b.selectbox("Outcome", ["offer_made", "callback", "saved", "lost"])
    offer = c.number_input("Offer (€/yr discount)", 0, 500, 0, step=10)
    notes = st.text_input("Notes")
    if st.form_submit_button("Record"):
        log_action(cust, os.environ.get("DATABRICKS_USER", "agent"), action, offer, notes)
        st.success(f"Logged {action} for {cust}")

if st.session_state.get("logged"):
    st.caption(f"Session actions logged: {len(st.session_state['logged'])}")
