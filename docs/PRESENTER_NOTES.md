# Streamline Telco Save Desk: presenter reading notes

**Total: about 25 minutes, plus questions.** Deck: `deck/Streamline-Telco-Save-Desk.pdf`. Demo: `app/simulator.html` (Chrome, full screen).

**In the room:** the **Chief Customer Officer** (business: funds the decision; owns churn and the retention budget) and the **Head of Data Platform** (technical: has to live with what we build). The **Head of Retention** runs the save desk; mention their team often.

**Three numbers to remember:** 45% vs 10% (churn after a switching mention) · 3.7× (precision of the call list vs random) · €5M net a year (−1 point of churn).

**Before you start:** open the PDF on slide 1. Open the simulator in a second tab on *Solution overview*, with the Demo script panel collapsed. Reload the simulator so the Lakebase table is empty.

How to read this: **SAY** = the words to use · **DO** = what to click · **IF ASKED** = short answers · **→** = transition.

---

## Part 1: Set-up and outcome (5 min)

### Slide 1: Keep the customers who are already telling us they will leave · 0:00–0:45
**SAY:** "Thank you for your time. In the next 25 minutes I want to show you how Streamline can keep the customers who are already telling you they are about to leave. I'll start with the outcome and what we found. Then a short live demo of the Save Desk, the architecture, the cost, and a plan to prove it in six weeks. Please interrupt me at any point."
**DO:** Look at both stakeholders and name what each will get: "For you, the business case and the KPIs. For you, how it is built and governed."
**→** "Let me start with the outcome."

### Slide 2: The outcome: one point less churn, €5M a year kept · 0:45–2:30
**SAY:** "Our target is one point of annual churn, from 16.8% to 15.8%. For Streamline that is 20,000 customers a year who stay: about €6.5 million of revenue protected, or about €5 million net after offers and the platform."
"For you as CCO, it is one number tracked every month against a control group, so it is measured, not forecast. For the retention team, every agent starts the day knowing who to call, why, and what to offer."
"And the cost: about $1.6k of compute for a six-week POC, about $3.5k a month in production at list price."
**KEY NUMBERS:** 16.8% → 15.8% · 20,000 · €6.5M (€5.0M net) · 6 weeks · 3.7×.
**IF ASKED "where do the numbers come from?":** "The model numbers are measured on the build. The business inputs (2 million subscribers, 1.4% monthly churn, €27 ARPU) are planning assumptions that we replace with your actuals in week 1."
**→** "Why is this possible now? Because today churn is visible too late."

### Slide 3: Today churn becomes visible only after the customer has left · 2:30–4:00
**SAY:** "Today the retention team sees churn when the porting request arrives, and by then the decision is made. The signals come earlier, in three places: what customers say on care calls, how the network performs for them, and what happens to their bill and contract. Nobody joins them up. So the team reacts late, offers are generic, and analysts wait days for a BI ticket."
**DO, ASK the CCO:** "Does this match what you see? How does your team find at-risk customers today?" *Listen; reuse their words later.*
**→** "We built this on synthetic data to see what the signals are worth."

### Slide 4: What we learned from the build · 4:00–5:30
**SAY:** "Three things stood out. One: customers who mention switching on a care call churn at 45%, against 10% for everyone else, more than four times higher. Two: if the save desk calls the model's top 10%, more than half are real churners, 3.7 times better than calling at random. Three: reading the calls is what makes the difference. When we remove the call features that Gen AI extracts, the model clearly gets worse. So the value of Gen AI is measured, not assumed."
**KEY LINE:** "The strongest predictor is what the customer says on the call. That signal is free; we only need to read it."
**IF ASKED (technical):** "Gradient boosting, 21 features, 5,000-subscriber hold-out. ROC-AUC 0.783 vs 0.729 without the call features; PR-AUC 0.49. On real data we expect lower numbers, so the POC gate is 2.5×, not 3.7×."
**→** "Let me show you what that looks like for the people who use it."

---

## Part 2: The demo, tell-show-tell (8 min)

### Slide 5: A day with the Save Desk · 5:30–6:15 (TELL)
**SAY:** "Here is a day with the Save Desk. At 2 a.m. the platform does the reading. At 8:30 the agent opens the save list. On the call they log the outcome. And at any time the manager can ask Genie. I'll show you exactly that: first, briefly, how the data gets there; then the agent's screen; then Genie. Watch for three things: who to call, why, and what to offer."
**DO:** Switch to the simulator tab.

### Demo step 1: Solution overview · 6:15–6:45
**DO:** Stay on *Solution overview*.
**SAY:** "This is Streamline's Databricks workspace. The whole solution is one journey: raw data, ingestion with Lakeflow, governance in Unity Catalog, AI reading the calls, the churn model, Lakebase and Genie, and the app. Everything you see runs on one platform."

### Demo step 2: Jobs & Pipelines › Run now · 6:45–7:45
**DO:** Click *Jobs & Pipelines* → **▶ Run now**. While it runs, click the **genai_enrichment** task.
**SAY:** "This is the nightly job. It runs at 2 a.m., deployed as code from one Asset Bundle. Ingest, read the calls with AI, apply governance, score every subscriber, refresh the app's database. Last night: 20,000 subscribers, 120,000 usage rows, 13,749 care calls."
**DO:** Open the tab **Lakeflow pipeline: save-desk-ingest**.
**SAY (for the technical stakeholder):** "Ingestion is a Lakeflow Declarative Pipeline. Auto Loader picks up new files incrementally, and these expectations are data-quality rules: a missing transcript or an implausible bill is dropped before it reaches the model. In production the files become Lakeflow Connect or Kafka feeds from billing, network and the contact centre. Nothing downstream changes."

### Demo step 3: AI Functions › Run · 7:45–8:30
**DO:** Click *AI Functions* → **▶ Run**. Let the rows appear; point at a negative call marked **1 · switching**.
**SAY:** "Here the AI reads every call, straight from SQL: sentiment, the reason for the call, and whether the customer is threatening to leave. This one is about a bill that nearly doubled, and the AI flags switching intent. The models are hosted in Databricks, so transcripts never leave the platform, and only new calls are processed each night."

### Demo step 4: Catalog › care_calls · 8:30–9:00
**DO:** Click *Catalog* → **raw › care_calls** → tab **Sample data**.
**SAY:** "Transcripts are the sensitive asset. I'm logged in as a retention user, so Unity Catalog masks the text: I see [REDACTED]. Only the data team sees it." **DO:** tab **Lineage** on *save_list*: "And lineage is automatic, from the raw files all the way to the app and Genie."
*(Optional, 20 s: Experiments & Models: "switch intent is the #1 driver, and the ablation on the right is the proof that reading the calls matters.")*

### Demo step 5: Apps › save-desk (the heart of the demo) · 9:00–11:30
**DO:** Click *Apps*.
**SAY:** "Now the agent's screen. This is a Databricks App. At the top: 1,825 subscribers at risk, about €838k of annual revenue in this sample. The list is ranked by value at risk, not only by probability."
**DO:** The first row, **STL102197**, is already open on the right.
**SAY:** "The top subscriber: an 89% chance of leaving in the next 60 days, €2,377 at stake. Why: they mentioned switching on a care call, and their bill went up 50%. So the next best offer is a loyalty price match, and here is a suggested opening line for the agent." *(Read the first sentence of the opening.)*
**DO:** Click **Offer accepted**.
**SAY:** "One click, and the outcome is saved." The counter shows 1 save and €2,682 of annual revenue kept.
**DO:** Filters: **All drivers → network**, **All regions → South**.
**SAY:** "Now the same list filtered by network problems in the South. A discount does not fix a dropped call. This list goes to the network team, not only to retention."
**DO:** Reset the filters (choose *All drivers*, *All regions*).

### Demo step 6: Lakebase · 11:30–12:00
**DO:** Click the link **view in Lakebase** in the green message (or *Lakebase* in the menu).
**SAY:** "And here is the outcome we just logged, written to Lakebase, the managed Postgres behind the app, in milliseconds. These outcomes flow back to the lakehouse, so every week the model learns which offers actually saved which customers."

### Demo step 7: Genie · 12:00–13:00
**DO:** Click *Genie* → the sample question **"What is the churn rate for customers who mentioned switching on a care call vs. those who did not?"**
**SAY:** "Finally, the manager. With Genie anyone can ask in plain English. The answer: 45% against 10%. And Genie shows the SQL behind it, so every answer can be checked." *(Optional: the network-region question → "the South".)*

### Back to slide 5 / TELL · 13:00–13:30
**DO:** Switch back to the deck.
**SAY:** "What you just saw is the difference between reacting to a porting request and calling a customer while there is still time. At 20,000 saves a year, that is €6.5 million of revenue."
**ASK:** "Is this how your retention team would want to work?"

---

## Part 3: How it is built (4 min, technical altitude)

### Slide 6: One governed journey from raw data to the agent's screen · 13:30–15:00
**SAY (technical):** "One journey, all on Databricks. Lakeflow ingests and checks quality. Unity Catalog governs everything: schemas, tags, masks, grants and lineage. AI Functions read the calls; the churn model is tracked in MLflow and registered in Unity Catalog. Lakebase serves the app with millisecond reads and takes the write-back. Genie answers on the same gold tables. The Databricks App is the agent's screen. It all deploys as one Asset Bundle."
**SAY (business, one line):** "For you, that means one platform, one copy of the data and one set of permissions."
**KEY POINTS:** integrated, not stitched · closed loop · production path without changes downstream.

### Slide 7: Security and governance by design · 15:00–16:00
**SAY:** "Transcripts are the sensitive asset, so they get the strictest controls: tagged, masked, visible only to the data team. Retention users and Genie see only the derived signals. The LLM runs on Databricks-hosted models, so no data goes to an outside API. For quality: pipeline expectations, LLM intent 95% aligned with the IVR queue in the build, and in the POC a check against 500 calls labelled by people, with a target of at least 85%."

### Slide 8: Decisions and trade-offs · 16:00–17:30
**SAY:** "These are the choices I would defend. AI Functions instead of a fine-tuned model: the task is generic, so we ship in days and keep everything governed; the cost is per token, which we manage by processing only new calls. Gradient boosting instead of deep learning, because agents need to know why they are calling. Lakebase for the app, because lookups and write-back are transactional work. Rule-based offers first, then an uplift model trained on real outcomes. Nightly batch first; real time later if the pilot shows same-day signals matter."
**→** "So what is it worth, what does it cost, and how do we prove it quickly?"

---

## Part 4: Value, cost and plan (6 min, business altitude)

### Slide 9: Value, cost and plan (divider) · 17:30
**SAY:** Use the transition line above; move on.

### Slide 10: Business case: about €5.0M net per year · 17:30–19:30
**SAY:** "The math is simple, and I want you to challenge every input. 2 million postpaid subscribers, 1.4% monthly churn: about 336,000 leave each year, about €109 million of revenue. To save 20,000, at a 25% save rate we need to reach 80,000 churners. With 56% precision that is about 143,000 calls a year, around 550 a day. 20,000 saves at €324 a year is €6.5 million. Offers cost about €1.4 million, because some go to customers who would have stayed. The platform is about €40k. Net: about €5 million a year, €73 per save."
**DOWNSIDE (say it before they ask):** "If the save rate is only half, the same calls still give about €2.2 million net."

### Slide 11: Cost: about $1.6k for the POC, $3.5k a month in production · 19:30–20:30
**SAY:** "The platform cost is small next to the value. About $1.6k of compute for the POC, about $3.5k a month in production at list price, about $42k a year. The biggest line is Gen AI on 690,000 calls a month; combining the three AI calls into one prompt brings the total to about $2.8k a month."
**BE HONEST:** "These are list-price estimates. Our team confirms them with a sizing tool before any quote; only the Foundation Model API rate is read directly from the public pricing page."

### Slide 12: Plan: prove it in six weeks, then scale with a control group · 20:30–22:00
**SAY:** "We de-risk in three steps, each with a go/no-go in your KPIs. POC, six weeks: prove the signal on your own history. The gate is 2.5× lift and 85% agreement with labels from people. Pilot, months 2 and 3: one region, 20 agents, a randomised control group. We go if the save rate beats control by at least 5 points at no more than €80 per save. Then scale from month 4. What we need from you: a sponsor, a retention lead who owns the offers, one data engineer, and approval to use three months of anonymised transcripts."

### Slide 13: Questions we expect, and our answers · only if needed
Use it only when questions come. Answer at the altitude of whoever asked (see the Q&A sheet below).

### Slide 14: The decision we are asking for · 22:00–23:00
**SAY:** "The ask is simple: approve a six-week POC, name a sponsor and a retention lead, and share three months of anonymised data. In six weeks you will know, on your own data, whether this list finds your churners."
**THEN STOP TALKING and ask:** "What would you need to see to approve the POC?"

### Slide 15: Appendix: build evidence and references, and Slide 16: closing
Reference only. Show slide 15 if someone asks "has this actually run?": "Every result is committed as text in the repository: the run log, the metrics, the Genie answers."

---

## Q&A sheet: lead with the conclusion, then one reason

**Business (CCO)**
| Question | Answer |
|---|---|
| Too expensive? | The platform is about $42k a year against about €5M net. The real cost is the offers, and the control group keeps that honest. |
| How fast is the value? | Six weeks to a back-tested list on your data; first measured saves in month 2. |
| It's synthetic data. | Yes, so the POC gate is lower (2.5×, not 3.7×) and is measured on your history before you commit more. |
| Are we just giving discounts away? | The offer follows the reason. A network fix costs €15; discounts go only to price-driven churners. |
| What if it doesn't work? | At half the save rate it is still about €2.2M net. If the POC misses its gate, we stop. |

**Technical (platform lead)**
| Question | Answer |
|---|---|
| Integration? | Lakeflow Connect or Kafka from billing, network probes and the contact-centre platform into the same bronze tables. Outcomes sit in Postgres, readable by the CRM. |
| Data quality? | Pipeline expectations; LLM labels checked against labels from people; drift and retraining tracked in MLflow. |
| Security / PII? | Transcripts tagged and masked in Unity Catalog; Databricks-hosted models; gold-only grants; the app runs as its own service principal; lineage end to end. |
| Why Lakebase, not Delta? | Millisecond lookups plus transactional write-back are OLTP work. A synced table keeps it declarative. |
| Why not real time? | Save decisions are daily, so batch is cheaper. Real-time scoring when a call ends is phase 3. |
| LLM cost at scale? | About $1.2k a month for 690,000 calls; one combined prompt cuts about 60%. |
| Lock-in? | Delta, Postgres and MLflow/scikit-learn are open. |
| Is this demo live? | It is a demo workspace replaying last night's run on synthetic data. The code in the repository deploys the same thing to a real workspace as one Asset Bundle. |

## Delivery reminders
- **Tell → show → tell:** say what you'll show, show it, then say what it means in euros and KPIs.
- **Switch altitude out loud:** "For you, [CCO], that means… and for you, [architect], the mechanism is…"
- Keep the demo to about 8 minutes, and don't explain every screen.
- If you lose your place in the demo, open the **Demo script** panel (bottom left) and click the next step.
- Close with the question, then wait.
