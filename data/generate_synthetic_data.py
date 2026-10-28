"""
FE Bar build — Streamline Telco "Save Desk" | Synthetic data generator
=======================================================================
Generates a fully synthetic, customer-SAFE dataset for a telecom
(consumer postpaid mobile + broadband) churn use case.
Streamline Telco is a fictional company. NO real customer data is used.

Produces the RAW landing files that Lakeflow ingests:
  - subscribers.parquet      one row per postpaid subscriber
  - usage.parquet            6 monthly usage + network-experience rows / sub
  - contracts.parquet        plan, price, handset / commitment end date
  - care_calls.parquet       inbound care calls WITH transcripts
  - churn_labels.parquet     ground truth: did the subscriber port out in next 60d

Churn comes from a latent risk model driven by real telco signals
(dropped calls, slow data, bill shock, commitment ending, competitor
mentions in care calls, low tenure), so the model trained downstream
recovers genuine, explainable patterns.

Run:  python data/generate_synthetic_data.py
"""
from __future__ import annotations
import json, random, datetime as dt
from pathlib import Path
import numpy as np
import pandas as pd

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

OUT = Path(__file__).resolve().parent / "output"
OUT.mkdir(parents=True, exist_ok=True)

N_SUBS = 20_000
REF_DATE = dt.date(2026, 9, 30)          # "today" for the snapshot
HISTORY_MONTHS = 6

REGIONS = {"North": 0.24, "Capital": 0.22, "Central": 0.18, "South": 0.20, "Islands": 0.08, "Coast": 0.08}
PLANS = {  # plan -> (monthly price EUR, data GB)
    "Mobile 10GB": (12.0, 10), "Mobile 50GB": (19.0, 50), "Mobile Unlimited": (29.0, 999),
    "Fibre + Mobile": (45.0, 999), "Fibre 1Gb": (32.0, 0),
}
PAYMENT = ["direct_debit", "card", "bank_transfer"]
CHANNELS = ["store", "online", "telesales", "comparison_site"]
QUEUES = ["billing", "network", "retention", "device", "general"]

# ---------------------------------------------------------------------------
# Care-call transcripts keyed to (intent, sentiment). Short and realistic.
# ---------------------------------------------------------------------------
TRANSCRIPTS = {
    ("billing", "negative"): [
        "My bill went up again this month, nearly double what I signed up for. This is ridiculous, explain it or I am leaving.",
        "You charged me roaming fees I never used. I am really annoyed, I am looking at other providers.",
        "Every month there is some new charge on my bill. If you cannot fix it I will cancel the contract.",
    ],
    ("billing", "neutral"): [
        "Hi, I would like to understand the extra line on my latest invoice.",
        "Can you confirm when my direct debit will be taken this month?",
    ],
    ("network", "negative"): [
        "My calls keep dropping at home and the signal is terrible. I pay for a service I do not get, this is unacceptable.",
        "Mobile data is so slow I cannot even load a map. Third time I call about it and nothing changes.",
        "The fibre goes down every evening. I work from home, I cannot keep living with these outages.",
    ],
    ("network", "neutral"): [
        "Is there any maintenance planned in my area this week? The signal was weak yesterday.",
        "I would like to check fibre availability at my new address.",
    ],
    ("retention", "negative"): [
        "Another operator offered me unlimited data for half the price. Match it or I am porting my number out.",
        "I want to cancel, I found a better deal elsewhere. Please send me my PAC code to switch.",
        "Your prices are no longer competitive. I am thinking of switching provider when my contract ends.",
    ],
    ("retention", "neutral"): [
        "My contract ends next month, what can you offer me to renew?",
        "Before I renew, are there better plans for how I use my phone?",
    ],
    ("device", "negative"): [
        "The phone you sold me is faulty and the repair is taking weeks. Very disappointed with the service.",
    ],
    ("device", "neutral"): [
        "Am I eligible for a handset upgrade yet?",
        "How do I activate the eSIM on my new phone?",
    ],
    ("general", "positive"): [
        "Thanks a lot, the agent was really helpful and fixed it straight away. Very happy with the service.",
        "I would like to add a second line for my daughter, I am very satisfied with you.",
    ],
    ("general", "neutral"): [
        "I just wanted to update my email address, thanks.",
        "Can you tell me how to set up voicemail?",
    ],
}
COMPETITOR_TERMS = ["other operator", "porting", "pac code", "switching provider", "other providers", "better deal", "cancel"]


def weighted(dic):
    ks = list(dic.keys()); ps = np.array(list(dic.values()), float); ps /= ps.sum()
    return np.random.choice(ks, p=ps)


def build_subscribers() -> pd.DataFrame:
    rows = []
    for i in range(N_SUBS):
        region = weighted(REGIONS)
        plan = random.choices(list(PLANS), weights=[0.18, 0.30, 0.22, 0.18, 0.12])[0]
        tenure = int(np.clip(np.random.gamma(2.0, 15), 1, 160))
        rows.append(dict(
            subscriber_id=f"STL{100000+i}",
            region=region,
            segment=random.choices(["consumer", "family", "youth"], weights=[0.62, 0.26, 0.12])[0],
            age_band=random.choices(["18-24", "25-34", "35-49", "50-64", "65+"], weights=[0.12, 0.24, 0.30, 0.22, 0.12])[0],
            payment_method=random.choices(PAYMENT, weights=[0.62, 0.28, 0.10])[0],
            acquisition_channel=random.choices(CHANNELS, weights=[0.34, 0.30, 0.16, 0.20])[0],
            tenure_months=tenure,
            plan=plan,
            lines=random.choices([1, 2, 3, 4], weights=[0.62, 0.22, 0.11, 0.05])[0],
        ))
    return pd.DataFrame(rows)


def build_contracts(subs: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for s in subs.itertuples():
        price, _ = PLANS[s.plan]
        commitment_end = REF_DATE + dt.timedelta(days=int(np.random.normal(260, 220)))
        rows.append(dict(
            contract_id=f"CTR{s.subscriber_id[3:]}", subscriber_id=s.subscriber_id,
            plan=s.plan, monthly_price_eur=round(price * s.lines * np.random.uniform(0.85, 1.1), 2),
            handset_financed=int(random.random() < 0.45),
            start_date=(REF_DATE - dt.timedelta(days=int(s.tenure_months * 30.4))).isoformat(),
            commitment_end_date=commitment_end.isoformat(), status="active",
        ))
    return pd.DataFrame(rows)


def build_usage(subs: pd.DataFrame, contr: pd.DataFrame) -> pd.DataFrame:
    """Monthly usage + network experience. A subset suffer degraded network
    (more dropped calls, slower data) or bill shock in the last 2 months."""
    price = contr.set_index("subscriber_id").monthly_price_eur
    months = pd.date_range(end=pd.Timestamp(REF_DATE).to_period("M").to_timestamp(),
                           periods=HISTORY_MONTHS, freq="MS")
    rows = []
    for s in subs.itertuples():
        bad_network = np.random.random() < (0.22 if s.region in ("South", "Islands") else 0.12)
        bill_shock = np.random.random() < 0.15
        _, gb = PLANS[s.plan]
        for k, m in enumerate(months):
            recent = k >= HISTORY_MONTHS - 2
            dropped = np.random.poisson(6 if (bad_network and recent) else 1.2)
            speed = max(2, np.random.normal(9 if (bad_network and recent) else 38, 6))
            bill = price[s.subscriber_id] * (np.random.uniform(1.25, 1.6) if (bill_shock and recent) else np.random.normal(1, 0.03))
            rows.append(dict(
                subscriber_id=s.subscriber_id, month=m.date().isoformat(),
                data_gb_used=round(max(0, np.random.normal(min(gb, 60) * 0.6, 5)), 1) if gb else 0.0,
                voice_minutes=int(max(0, np.random.normal(320, 110))),
                dropped_calls=int(dropped), avg_dl_speed_mbps=round(speed, 1),
                bill_amount_eur=round(bill, 2),
            ))
    return pd.DataFrame(rows)


def build_calls_and_churn(subs, contr, usage):
    """Care calls with transcripts + latent churn. Signals in calls, network
    and billing line up with the churn label so the model is real."""
    u = usage.sort_values(["subscriber_id", "month"])
    last2 = u.groupby("subscriber_id").tail(2).groupby("subscriber_id")
    first4 = u.groupby("subscriber_id").head(4).groupby("subscriber_id")
    dropped = last2.dropped_calls.mean()
    speed = last2.avg_dl_speed_mbps.mean()
    bill_trend = (last2.bill_amount_eur.mean() - first4.bill_amount_eur.mean()) / first4.bill_amount_eur.mean()
    cend = contr.set_index("subscriber_id").commitment_end_date

    call_rows, churn_rows = [], []
    for s in subs.itertuples():
        sid = s.subscriber_id
        dr, sp, bt = float(dropped[sid]), float(speed[sid]), float(bill_trend[sid])
        days_to_end = (dt.date.fromisoformat(cend[sid]) - REF_DATE).days
        net_pain = dr > 3.5 or sp < 15
        # latent churn propensity --------------------------------------------
        z = -2.6
        z += 0.12 * max(0, dr - 1.5) + (0.7 if sp < 15 else 0)
        z += 2.0 * max(0, bt)
        z += 0.8 if 0 <= days_to_end < 60 else (0.4 if days_to_end < 0 else 0)   # out of contract = free to leave
        z += -0.01 * s.tenure_months
        z += 0.45 if s.acquisition_channel == "comparison_site" else 0
        z += -0.35 if s.lines > 1 else 0
        z += 0.3 if s.payment_method == "card" else 0

        lam = 0.4 + (1.0 if net_pain else 0) + 1.5 * max(0, bt) + (0.5 if 0 <= days_to_end < 60 else 0)
        n_calls = np.random.poisson(lam)
        neg = ret = comp = 0
        for _ in range(n_calls):
            if net_pain and random.random() < 0.55: intent = "network"
            elif bt > 0.15 and random.random() < 0.6: intent = "billing"
            elif days_to_end < 60 and random.random() < 0.45: intent = "retention"
            else: intent = random.choices(QUEUES, weights=[0.25, 0.20, 0.10, 0.20, 0.25])[0]
            unhappy_p = 1 / (1 + np.exp(-(z + 0.8)))
            if intent in ("billing", "network", "retention", "device"):
                sentiment = "negative" if random.random() < min(0.85, 0.3 + unhappy_p) else "neutral"
            else:
                sentiment = "positive" if random.random() < 0.35 else "neutral"
            key = (intent, sentiment) if (intent, sentiment) in TRANSCRIPTS else (intent, "neutral")
            if key not in TRANSCRIPTS: key = ("general", "neutral")
            text = random.choice(TRANSCRIPTS[key])
            c = int(any(t in text.lower() for t in COMPETITOR_TERMS))
            comp = max(comp, c); neg += sentiment == "negative"; ret += intent == "retention"
            ts = dt.datetime.combine(REF_DATE - dt.timedelta(days=random.randint(0, 59)),
                                     dt.time(random.randint(8, 20), random.randint(0, 59)))
            call_rows.append(dict(
                call_id=f"CALL{len(call_rows)+1:07d}", subscriber_id=sid, call_ts=ts.isoformat(),
                queue=intent, agent_id=f"AG{random.randint(1, 220):03d}",
                duration_sec=int(np.clip(np.random.normal(240, 100), 30, 1200)), transcript=text,
            ))
        z += 0.5 * neg + 0.7 * ret + 0.9 * comp
        p = 1 / (1 + np.exp(-z))
        churn_rows.append(dict(subscriber_id=sid, churned_next_60d=int(random.random() < p), _latent_p=round(p, 4)))
    return pd.DataFrame(call_rows), pd.DataFrame(churn_rows)


def main():
    log = []
    def note(m):
        print(m); log.append(m)

    note(f"[gen] seed={SEED}  ref_date={REF_DATE}  subscribers={N_SUBS}")
    subs = build_subscribers();                 note(f"[gen] subscribers    -> {len(subs):>7,} rows")
    contr = build_contracts(subs);              note(f"[gen] contracts      -> {len(contr):>7,} rows")
    usage = build_usage(subs, contr);           note(f"[gen] usage          -> {len(usage):>7,} rows")
    calls, churn = build_calls_and_churn(subs, contr, usage)
    note(f"[gen] care_calls     -> {len(calls):>7,} rows")
    note(f"[gen] churn_labels   -> {len(churn):>7,} rows")
    rate = churn.churned_next_60d.mean()
    note(f"[gen] churn rate (synthetic, next 60d) = {rate:.3%}")

    for name, df in [("subscribers", subs), ("contracts", contr), ("usage", usage),
                     ("care_calls", calls), ("churn_labels", churn)]:
        df.to_parquet(OUT / f"{name}.parquet", index=False)
        df.head(50).to_csv(OUT / f"{name}_sample.csv", index=False)
    note(f"[gen] wrote parquet + *_sample.csv to data/output/")

    (OUT / "generation.log").write_text("\n".join(log) + "\n")
    meta = dict(company="Streamline Telco (fictional)", seed=SEED, ref_date=REF_DATE.isoformat(),
                n_subscribers=N_SUBS, churn_rate_60d=round(float(rate), 4),
                tables={n: int(len(d)) for n, d in [("subscribers", subs), ("contracts", contr),
                        ("usage", usage), ("care_calls", calls), ("churn_labels", churn)]})
    (OUT / "dataset_meta.json").write_text(json.dumps(meta, indent=2))
    note("[gen] done.")


if __name__ == "__main__":
    main()
