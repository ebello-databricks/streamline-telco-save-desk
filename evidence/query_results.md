# Genie agent questions — answered over the GOLD layer (run evidence)

> Produced by `data/run_local_pipeline.py` on synthetic data. In the workspace the Genie agent generates equivalent SQL over `streamline_telco.gold.*` (see `genie/genie_space_config.json`).

## Q1 — How many subscribers are High or Critical risk, and how much annual revenue do they represent?

```sql
SELECT risk_band, COUNT(*) subs, SUM(annual_value_eur) revenue FROM gold.save_list WHERE risk_band IN ('High','Critical') GROUP BY risk_band
```

```
           subs  revenue_eur
risk_band                   
Critical    799     362126.0
High       1026     475678.0
```

## Q2 — Which region has the most at-risk subscribers because of network problems?

```sql
SELECT region, COUNT(*) FROM gold.save_list WHERE risk_band IN ('High','Critical') AND driver='network' GROUP BY region ORDER BY 2 DESC
```

```
         at_risk_network
region                  
South                183
North                148
Capital              112
Central              105
Islands               93
Coast                 42
```

## Q3 — Show the 10 subscribers with the highest value at risk and what we should offer them.

```sql
SELECT subscriber_id, plan, churn_probability, value_at_risk_eur, next_best_offer FROM gold.save_list ORDER BY value_at_risk_eur DESC LIMIT 10
```

```
subscriber_id           plan  churn_probability  value_at_risk_eur                          next_best_offer
    STL102197 Fibre + Mobile             0.8861             2377.0 Loyalty price match (-20% for 12 months)
    STL108408 Fibre + Mobile             0.7499             1972.0 Loyalty price match (-20% for 12 months)
    STL102484 Fibre + Mobile             0.6751             1775.0 Loyalty price match (-20% for 12 months)
    STL111856 Fibre + Mobile             0.7072             1603.0       Early renewal with handset upgrade
    STL112387 Fibre + Mobile             0.7365             1409.0             Network fix + 1 month credit
    STL109097      Fibre 1Gb             0.8660             1331.0             Network fix + 1 month credit
    STL105965 Fibre + Mobile             0.5632             1316.0     Priority care callback + bill credit
    STL117766 Fibre + Mobile             0.5572             1312.0             Network fix + 1 month credit
    STL110863 Fibre + Mobile             0.7253             1268.0 Loyalty price match (-20% for 12 months)
    STL111916 Fibre + Mobile             0.7093             1253.0 Loyalty price match (-20% for 12 months)
```

## Q4 — What is the actual churn rate for customers who mentioned switching on a care call vs. those who did not?

```sql
SELECT switch_intent, AVG(churned_next_60d) FROM gold.subscriber_features GROUP BY switch_intent
```

```
               churn_rate_%
switch_intent              
0                      10.4
1                      45.2
```

## Q5 — Churn rate by plan

```sql
SELECT plan, AVG(churned_next_60d)*100 FROM gold.subscriber_features GROUP BY plan ORDER BY 2 DESC
```

```
                  churn_rate_%
plan                          
Mobile 50GB               15.8
Fibre + Mobile            15.2
Fibre 1Gb                 15.2
Mobile Unlimited          14.9
Mobile 10GB               14.0
```
