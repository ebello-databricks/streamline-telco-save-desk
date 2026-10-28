# AI role-play guide (20–30 min)

## Audience
| Persona | Role (assumed) | Cares about | Pitch at |
|---|---|---|---|
| Business stakeholder | Chief Customer Officer (executive sponsor; owns churn and the retention budget) | churn %, revenue kept, cost per save, time to value, risk | outcome, € and KPIs; one sentence on how |
| Technical stakeholder | Head of Data Platform / enterprise architect | integration, data quality, security, cost, lock-in, operability | mechanism, controls, trade-offs |
| Domain owner (mentioned, not in the room) | Head of Retention / save desk | save rate, agent productivity, offer catalogue | the agent's day |

The FE Bar picks the persona names for the industry; adapt to whoever introduces themselves.

## Run of show (open the PDF deck and app/demo.html)
1. **Set-up (1 min), slide 1:** who we are, who they are, the agenda, "interrupt me".
2. **Outcome first (2 min), slide 2:** −1 pt churn, 20,000 kept, €6.5M (€5.0M net), 6-week POC at ≈$1.6k.
3. **Problem (2 min), slide 3:** churn is seen only at porting; the signals sit in 3 systems. *Ask the CCO how they find at-risk customers today.*
4. **What we found (2 min), slide 4:** 45% vs 10%, 3.7× lift, Gen AI measured at +0.053 AUC.
5. **Demo, tell-show-tell (6 min), slide 5 then the app:**
   - Tell: "Three things to watch: who to call, why, what to offer."
   - Show: Save list → STL102197 (89%, €2,377 at risk, bill up 50%, mentioned switching) → loyalty price match → read the opening line → **Offer accepted** (Lakebase write-back, counter moves).
   - Show: filters driver = network, region = South: "a discount won't fix a dropped call; this list goes to the network team."
   - Show: Ask Genie → the switching question → 45.2% vs 10.4% with the SQL.
   - Tell: "From reacting to a porting request to calling while there is still time. 20,000 saves = €6.5M."
6. **Architecture and security (3 min), slides 6–7:** technical altitude, then one business sentence.
7. **Value, cost, plan (4 min), slides 10–12.**
8. **Ask (1 min), slide 14:** approve the 6-week POC; name a sponsor and a retention lead. *Then stop and ask what they need to approve.*

## Objection handling
**Business (CCO)**
- *"Too expensive / what does it cost?"* Platform ≈ $42k a year at list price against ≈ €5M net. The real cost is offers (€1.42M), and a control group keeps that honest.
- *"How long until I see value?"* 6 weeks to a back-tested list on your data; measured saves in month 2.
- *"Your numbers are on fake data."* Yes, so the POC gate is set lower (2.5× lift, not 3.7×) and is measured on your history before you commit more.
- *"Aren't we just giving discounts away?"* The offer follows the reason: a network fix costs €15. Discounts go only to price-driven churners.
- *"What if it doesn't work?"* At half the save rate it is still ≈ €2.2M net; and if the POC misses its gate, we stop.

**Technical (platform lead)**
- *Integration:* Lakeflow Connect or Kafka from billing, the network probes and the CCaaS platform into the same bronze tables; outcomes in Lakebase Postgres, readable by the CRM.
- *Data quality:* Lakeflow expectations; LLM intent 95% aligned with the IVR queue in the build, 500 calls labelled by people in the POC; drift and retraining in MLflow.
- *Security / PII:* transcripts tagged and masked in Unity Catalog; Databricks-hosted models (no external API); gold-only grants; the app runs as a service principal; lineage end to end.
- *Why Lakebase and not Delta?* Millisecond point lookups plus transactional write-back are OLTP; a synced table keeps it declarative.
- *Why not real time?* Save decisions are daily, so batch is cheaper; real-time scoring on call end is phase 3 (Model Serving).
- *LLM cost at scale?* ≈ $1.2k/month for 690k calls; one combined JSON prompt cuts it about 60%.
- *Lock-in?* Delta, Postgres and MLflow/scikit-learn are open.

## Delivery tips
Switch altitude explicitly: "For you, [CCO], that means… and for you, [architect], the mechanism is…". Keep the demo to 6 minutes. Lead every answer with the conclusion.
