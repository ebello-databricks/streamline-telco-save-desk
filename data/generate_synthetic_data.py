"""
FE Bar build — Plenitude "Voice-to-Retention" | Synthetic data generator
=========================================================================
Generates a fully synthetic, customer-SAFE dataset for a retail-energy
(Plenitude / Eni B2C) churn use case. NO real customer data is used.

Produces the RAW landing tables that Lakeflow ingests:
  - customers.parquet        one row per B2C energy customer
  - consumption.parquet      12 monthly bills per customer
  - contracts.parquet        one active contract per customer
  - calls.parquet            inbound contact-centre calls WITH transcripts
  - churn_labels.parquet     ground-truth: did the customer leave in next 90d

Churn is generated from a latent risk model driven by real-world signals
(negative call sentiment, retention-queue calls, bill shock, contract
near expiry, payment method, tenure, competitor mentions), so a model
trained downstream recovers genuine, explainable patterns.

Run:  python generate_synthetic_data.py
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

N_CUSTOMERS = 15_000
REF_DATE = dt.date(2026, 6, 30)          # "today" for the snapshot
HISTORY_MONTHS = 12

REGIONS = {
    "Lombardia": 0.19, "Lazio": 0.12, "Campania": 0.10, "Sicilia": 0.09,
    "Veneto": 0.09, "Emilia-Romagna": 0.08, "Piemonte": 0.08, "Puglia": 0.07,
    "Toscana": 0.07, "Calabria": 0.04, "Liguria": 0.03, "Altre": 0.04,
}
CITY = {
    "Lombardia": "Milano", "Lazio": "Roma", "Campania": "Napoli", "Sicilia": "Palermo",
    "Veneto": "Verona", "Emilia-Romagna": "Bologna", "Piemonte": "Torino", "Puglia": "Bari",
    "Toscana": "Firenze", "Calabria": "Reggio Calabria", "Liguria": "Genova", "Altre": "Perugia",
}
PRODUCTS = ["power", "gas", "dual"]
CONTRACT_TYPES = ["fixed", "variable"]
PAYMENT = ["direct_debit", "bank_transfer", "postal", "card"]
CHANNELS = ["web", "agency", "call_center", "comparator", "partner"]
QUEUES = ["billing", "technical", "retention", "commercial", "self_service"]

# ---------------------------------------------------------------------------
# Contact-centre transcript templates, keyed to (intent, sentiment).
# Italian, short, realistic. English gloss kept in a comment for the deck.
# ---------------------------------------------------------------------------
TRANSCRIPTS = {
    ("billing", "negative"): [
        "Buongiorno, ho ricevuto una bolletta di 240 euro, il triplo del solito. È assurdo, voglio spiegazioni o cambio fornitore.",
        "La fattura di questo mese è sbagliata, il conguaglio è troppo alto. Sono molto arrabbiato, sto valutando di andare da Enel.",
        "Non capisco perché pago sempre di più, gli importi continuano a salire. Se non risolvete disdico il contratto.",
    ],
    ("billing", "neutral"): [
        "Salve, vorrei capire meglio le voci in bolletta, in particolare gli oneri di sistema.",
        "Buongiorno, volevo verificare la data di scadenza della fattura di giugno.",
    ],
    ("retention", "negative"): [
        "Ho ricevuto un'offerta da un altro operatore molto più conveniente. Se non mi allineate il prezzo passo alla concorrenza.",
        "Voglio disdire il contratto, ho trovato di meglio altrove. La vostra tariffa non è più competitiva.",
        "Sto pensando di cambiare fornitore, il prezzo del kWh è troppo alto rispetto al mercato.",
    ],
    ("retention", "neutral"): [
        "Vorrei sapere se ci sono offerte migliori per il mio profilo di consumo prima del rinnovo.",
        "Il mio contratto è in scadenza, che condizioni mi proponete per il rinnovo?",
    ],
    ("technical", "negative"): [
        "Sono senza corrente da due giorni e nessuno mi ha richiamato. Servizio pessimo, così non va bene.",
        "Il contatore dà errore e ho segnalato tre volte senza risposta. Sono stanco di questi disservizi.",
    ],
    ("technical", "neutral"): [
        "Buongiorno, vorrei prenotare la lettura del contatore per l'autolettura.",
        "Salve, ho bisogno di assistenza per attivare l'app e vedere i consumi.",
    ],
    ("commercial", "positive"): [
        "Grazie mille, l'operatore è stato gentilissimo e ha risolto subito. Sono molto soddisfatto del servizio.",
        "Volevo aggiungere la fornitura gas alla mia utenza luce, mi trovo benissimo con voi.",
    ],
    ("commercial", "neutral"): [
        "Vorrei attivare la fornitura per la mia seconda casa, che documenti servono?",
        "Buongiorno, come posso attivare la fatturazione elettronica e il pagamento con addebito?",
    ],
    ("self_service", "neutral"): [
        "Volevo solo comunicare l'autolettura del contatore, grazie.",
        "Confermo l'appuntamento per il tecnico, tutto ok.",
    ],
}
COMPETITOR_TERMS = ["Enel", "concorrenza", "altro operatore", "cambio fornitore", "disdire"]


def weighted(dic):
    ks = list(dic.keys()); ps = np.array(list(dic.values()), float); ps /= ps.sum()
    return np.random.choice(ks, p=ps)


def build_customers() -> pd.DataFrame:
    rows = []
    for i in range(N_CUSTOMERS):
        region = weighted(REGIONS)
        product = random.choices(PRODUCTS, weights=[0.42, 0.18, 0.40])[0]
        ctype = random.choices(CONTRACT_TYPES, weights=[0.55, 0.45])[0]
        segment = random.choices(["residential", "microbusiness"], weights=[0.86, 0.14])[0]
        tenure = int(np.clip(np.random.gamma(2.2, 14), 1, 180))
        pay = random.choices(PAYMENT, weights=[0.52, 0.20, 0.10, 0.18])[0]
        channel = random.choices(CHANNELS, weights=[0.30, 0.22, 0.18, 0.18, 0.12])[0]
        base_bill = {"power": 68, "gas": 74, "dual": 128}[product]
        base_bill *= (1.9 if segment == "microbusiness" else 1.0)
        monthly_bill = round(max(18, np.random.normal(base_bill, base_bill * 0.28)), 2)
        contract_end = REF_DATE + dt.timedelta(days=int(np.random.normal(300, 210)))
        rows.append(dict(
            customer_id=f"PLN{100000+i}",
            region=region, city=CITY[region], segment=segment,
            product=product, contract_type=ctype, payment_method=pay,
            signup_channel=channel, ebilling=int(random.random() < 0.58),
            tenure_months=tenure, monthly_bill_eur=monthly_bill,
            contract_end_date=contract_end.isoformat(),
        ))
    return pd.DataFrame(rows)


def build_consumption(cust: pd.DataFrame) -> pd.DataFrame:
    rows = []
    months = pd.date_range(end=pd.Timestamp(REF_DATE).to_period("M").to_timestamp(),
                           periods=HISTORY_MONTHS, freq="MS")
    for c in cust.to_dict('records'):
        c = type('R', (), c)  # dot-access wrapper
        # seasonal shape (winter heating for gas/dual, summer cooling for power)
        base = c.monthly_bill_eur
        # a subset get a "bill shock" ramp in the last 3 months -> churn driver
        shock = np.random.random() < 0.22
        for k, m in enumerate(months):
            season = 1.0 + 0.22 * np.sin((m.month - 1) / 12 * 2 * np.pi + (0 if c.product == "power" else np.pi))
            trend = 1.0
            if shock and k >= HISTORY_MONTHS - 3:
                trend = 1.0 + 0.18 * (k - (HISTORY_MONTHS - 4))
            amt = round(max(10, base * season * trend * np.random.normal(1, 0.06)), 2)
            kwh = round(amt / 0.31 * np.random.normal(1, 0.05), 1) if c.product != "gas" else 0.0
            smc = round(amt / 1.05 * np.random.normal(1, 0.05), 1) if c.product != "power" else 0.0
            rows.append(dict(customer_id=c.customer_id, month=m.date().isoformat(),
                             bill_amount_eur=amt, kwh=kwh, smc_gas=smc))
    return pd.DataFrame(rows)


def build_contracts(cust: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for c in cust.to_dict('records'):
        c = type('R', (), c)
        start = REF_DATE - dt.timedelta(days=int(c.tenure_months * 30.4))
        tariff = round(np.random.uniform(0.089, 0.164), 3) if c.product != "gas" else round(np.random.uniform(0.42, 0.78), 3)
        rows.append(dict(
            contract_id=f"CNT{c.customer_id[3:]}", customer_id=c.customer_id,
            product=c.product, contract_type=c.contract_type,
            start_date=start.isoformat(), end_date=c.contract_end_date,
            unit_tariff=tariff, status="active",
        ))
    return pd.DataFrame(rows)


def build_calls_and_churn(cust: pd.DataFrame, cons: pd.DataFrame):
    """Generate calls with transcripts + latent churn. Signals in the calls
    and billing must line up with the churn label so the model is real."""
    # precompute recent bill trend per customer (last 3 vs prior 3)
    cons_sorted = cons.sort_values(["customer_id", "month"])
    last3 = cons_sorted.groupby("customer_id").tail(3).groupby("customer_id").bill_amount_eur.mean()
    prev3 = (cons_sorted.groupby("customer_id").apply(lambda g: g.iloc[-6:-3].bill_amount_eur.mean(),
             include_groups=False))
    bill_trend = ((last3 - prev3) / prev3.clip(lower=1)).fillna(0)

    call_rows, churn_rows = [], []
    for c in cust.to_dict('records'):
        c = type('R', (), c)
        cid = c.customer_id
        trend = float(bill_trend.get(cid, 0.0))
        days_to_end = (dt.date.fromisoformat(c.contract_end_date) - REF_DATE).days

        # latent churn propensity ---------------------------------------
        z = -2.15
        z += 2.2 * max(0, trend)                       # bill shock
        z += 0.9 if c.contract_type == "variable" else 0.0
        z += 0.6 if c.payment_method in ("postal", "card") else -0.35 if c.payment_method == "direct_debit" else 0.0
        z += 0.5 if days_to_end < 90 else 0.0
        z += -0.012 * c.tenure_months                  # loyalty
        z += 0.4 if c.signup_channel == "comparator" else 0.0
        z += -0.3 if c.ebilling else 0.0

        # number of calls in last 90 days, more if unhappy
        lam = 0.5 + 1.6 * max(0, trend) + (0.4 if days_to_end < 90 else 0)
        n_calls = np.random.poisson(lam)
        neg_calls = 0; retention_calls = 0; competitor_mention = 0
        sent_scores = []
        for j in range(n_calls):
            # pick intent influenced by the customer's situation
            if trend > 0.12 and random.random() < 0.6:
                intent = "billing"
            elif days_to_end < 90 and random.random() < 0.5:
                intent = "retention"
            else:
                intent = random.choices(QUEUES, weights=[0.30, 0.22, 0.14, 0.16, 0.18])[0]
            # sentiment influenced by propensity
            unhappy_p = 1 / (1 + np.exp(-(z + 0.6)))
            if intent in ("billing", "retention", "technical"):
                sentiment = "negative" if random.random() < min(0.85, 0.35 + unhappy_p) else "neutral"
            elif intent == "commercial":
                sentiment = "positive" if random.random() < 0.6 else "neutral"
            else:
                sentiment = "neutral"
            key = (intent, sentiment)
            if key not in TRANSCRIPTS:
                key = (intent, "neutral") if (intent, "neutral") in TRANSCRIPTS else ("self_service", "neutral")
            transcript = random.choice(TRANSCRIPTS[key])
            comp = int(any(t.lower() in transcript.lower() for t in COMPETITOR_TERMS))
            competitor_mention = max(competitor_mention, comp)
            if sentiment == "negative": neg_calls += 1
            if intent == "retention": retention_calls += 1
            sent_scores.append({"negative": -0.8, "neutral": 0.05, "positive": 0.7}[sentiment]
                               + np.random.normal(0, 0.08))
            call_ts = REF_DATE - dt.timedelta(days=random.randint(0, 89),
                                              hours=random.randint(8, 19))
            call_rows.append(dict(
                call_id=f"CALL{len(call_rows)+1:07d}", customer_id=cid,
                call_ts=dt.datetime.combine(call_ts if isinstance(call_ts, dt.date) else REF_DATE, dt.time(random.randint(8,19), random.randint(0,59))).isoformat(),
                queue=intent, agent_id=f"AG{random.randint(1,180):03d}",
                duration_sec=int(np.clip(np.random.normal(210, 90), 30, 900)),
                transcript=transcript,
            ))

        # calls feed back into churn propensity
        z += 0.55 * neg_calls + 0.8 * retention_calls + 0.7 * competitor_mention
        churn_p = 1 / (1 + np.exp(-z))
        churned = int(random.random() < churn_p)
        churn_rows.append(dict(customer_id=cid, churned_next_90d=churned,
                               _latent_p=round(churn_p, 4)))

    return pd.DataFrame(call_rows), pd.DataFrame(churn_rows)


def main():
    log = []
    def note(m):
        print(m); log.append(m)

    note(f"[gen] seed={SEED}  ref_date={REF_DATE}  customers={N_CUSTOMERS}")
    cust = build_customers();                 note(f"[gen] customers      -> {len(cust):>7,} rows")
    cons = build_consumption(cust);           note(f"[gen] consumption    -> {len(cons):>7,} rows")
    contr = build_contracts(cust);            note(f"[gen] contracts      -> {len(contr):>7,} rows")
    calls, churn = build_calls_and_churn(cust, cons)
    note(f"[gen] calls          -> {len(calls):>7,} rows")
    note(f"[gen] churn_labels   -> {len(churn):>7,} rows")

    rate = churn.churned_next_90d.mean()
    note(f"[gen] churn rate (synthetic 90d) = {rate:.3%}")
    note(f"[gen] negative-call customers    = {calls.assign(neg=calls.transcript.isin([t for k,v in TRANSCRIPTS.items() if k[1]=='negative' for t in v])).groupby('customer_id').neg.max().mean():.1%}")

    # write parquet (efficient) + small CSV samples (human/text readable)
    for name, df in [("customers", cust), ("consumption", cons), ("contracts", contr),
                     ("calls", calls), ("churn_labels", churn)]:
        df.to_parquet(OUT / f"{name}.parquet", index=False)
        df.head(50).to_csv(OUT / f"{name}_sample.csv", index=False)
    note(f"[gen] wrote parquet + *_sample.csv to {OUT}")

    (OUT / "generation.log").write_text("\n".join(log) + "\n")
    meta = dict(seed=SEED, ref_date=REF_DATE.isoformat(), n_customers=N_CUSTOMERS,
                churn_rate=round(float(rate), 4),
                tables={n: int(len(d)) for n, d in
                        [("customers", cust), ("consumption", cons), ("contracts", contr),
                         ("calls", calls), ("churn_labels", churn)]})
    (OUT / "dataset_meta.json").write_text(json.dumps(meta, indent=2))
    note("[gen] done.")


if __name__ == "__main__":
    main()
