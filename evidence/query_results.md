# Query results (GOLD layer) — committed run evidence

> Produced by `data/run_local_pipeline.py`. In the workspace these are Databricks SQL / Genie answers over the same gold tables.

## Q1 — Customers by risk band
```
           customers
risk_band           
Critical         497
High            1104
Medium          2735
Low            10664
```

## Q2 — Top 10 at-risk customers (retention call list)
```
customer_id         region       segment product  monthly_bill_eur  churn_probability risk_band                                                        top_reasons  n_negative_calls  n_retention_calls  churn_mentions
  PLN110827          Altre   residential   power             78.73             0.9730  Critical called retention line; mentioned switching/competitor; bill up 47%               3.0                1.0             1.0
  PLN100143        Sicilia microbusiness   power            154.39             0.9710  Critical called retention line; mentioned switching/competitor; bill up 62%               1.0                2.0             1.0
  PLN102474       Campania   residential     gas            101.50             0.9692  Critical called retention line; mentioned switching/competitor; bill up 30%               1.0                1.0             1.0
  PLN104496      Lombardia   residential   power             66.21             0.9644  Critical called retention line; mentioned switching/competitor; bill up 58%               2.0                1.0             1.0
  PLN109154 Emilia-Romagna   residential   power             96.58             0.9642  Critical called retention line; mentioned switching/competitor; bill up 11%               1.0                2.0             1.0
  PLN107636          Lazio   residential   power             53.82             0.9597  Critical called retention line; mentioned switching/competitor; bill up 41%               3.0                2.0             1.0
  PLN110354      Lombardia   residential   power             43.40             0.9597  Critical    mentioned switching/competitor; bill up 43%; 1 negative call(s)               1.0                0.0             1.0
  PLN113697        Toscana   residential   power             69.84             0.9597  Critical called retention line; mentioned switching/competitor; bill up 11%               2.0                3.0             1.0
  PLN103490 Emilia-Romagna   residential   power             74.76             0.9583  Critical called retention line; mentioned switching/competitor; bill up 53%               1.0                2.0             1.0
  PLN107729       Calabria   residential   power             84.94             0.9581  Critical called retention line; mentioned switching/competitor; bill up 11%               1.0                2.0             1.0
```

## Q3 — Churn rate by region (highest first)
```
                churn_rate_%
region                      
Altre                   23.8
Liguria                 23.6
Puglia                  23.5
Campania                22.8
Lombardia               22.7
Lazio                   22.3
Emilia-Romagna          22.1
Toscana                 21.9
Veneto                  21.9
Sicilia                 21.8
Piemonte                21.5
Calabria                19.1
```

## Q4 — Avg churn probability by contract type & payment method
```
pay_risky          0      1
contract_type              
fixed          0.138  0.254
variable       0.249  0.396
```

## Q5 — Value at risk in the Critical + High bands
```
customers at risk (Critical+High): 1,601
annual revenue represented        : EUR 1,910,374
(gross-margin @ 22% ≈ EUR 420,282 of margin exposed)
```
