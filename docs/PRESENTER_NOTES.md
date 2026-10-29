# Streamline Telco Save Desk: presenter reading notes

**Time:** about 20 minutes of talk. The session is 20–30 minutes, so this leaves time for questions.
**Deck:** the **Google Slides** version, *Streamline Telco - Save Desk (FE Bar)*, in presenter mode.
**Demo:** `app/simulator.html` in Chrome, full screen.

**Who is in the room (two AI personas):**
- The **Chief Customer Officer (CCO)**. Business person. Owns churn and the retention budget. Decides and pays.
- The **Head of Data Platform**. Technical person. Will run what we build.
- The **Head of Retention** runs the save desk. They are not in the room, but mention their team often.

**Three numbers to remember:** 45% vs 10% · 3.7 times · 5 million euros net a year.

## How to present to an AI
- **You lead.** The AI will not interrupt much. Do not ask questions and wait. Ask only one question, at the end.
- **Say what you see.** When you click, read the number on the screen out loud. The AI may not see your screen.
- **Say the structure out loud:** "First I tell you what I will show." → "Now I show it." → "This is what it means for you."
- **Say who you are talking to:** "For you, as CCO…" and "For you, as Head of Data Platform…"
- **Answer objections before they come.** Look for the **OBJECTION** lines below.
- **If they ask a question:** give the answer first, then one reason. Then stop.

**Before you start:**
1. Open the Google Slides deck on slide 1, in presenter mode.
2. Open the simulator in a second tab, on *Solution overview*.
3. Press Cmd + R on the simulator, so it starts empty.

**Slide order (the demo is at the end, so just go to the next slide each time):**
1. Slides 1–4: introduction and result
2. Slides 5–7: how it is built
3. Slides 8–11: value, cost and plan
4. Slide 12, then the live demo in the simulator
5. Slide 13: the decision
6. Slides 14–16: only if needed (questions, appendix, closing)

**Key:** **SAY** = read this · **DO** = click this · **OBJECTION** = answer it before they ask · **→** = move to the next slide.

---

## Part 1: Introduction and outcome (4 minutes)

### Slide 1: Keep the customers who are already telling us they will leave · 0:00–1:00
**SAY:** "Good morning, and thank you for your time. My name is Emmanuele Bello. I am a Delivery Solutions Architect at Databricks, and I am based in Italy. I work with large companies in Southern Europe. I help them take data and AI projects from the first idea to production, and I make sure they deliver real value. I built the solution you will see today."
**SAY:** "Today I want to show you how Streamline can keep the customers who are telling you they want to leave. First, the result and what we learned. Then how it is built and protected. Then the value, the cost and a six-week plan. And at the end, a short live demo, so you can see it working."
**SAY:** "For you, as CCO, I will focus on the business case and the numbers. For you, as Head of Data Platform, I will focus on how it is built, how it is secured, and how it runs."
**→** "Let me start with the result."

### Slide 2: The outcome: one point less churn, €5M a year kept · 1:00–2:30
**SAY:** "Our goal is to reduce churn by one point. From 16.8% to 15.8% a year. For Streamline, this means 20,000 customers stay every year. That is about 6.5 million euros of revenue. After the cost of the offers and the platform, it is about 5 million euros net."
**SAY:** "For you, as CCO, this is one number. We measure it every month against a control group. So it is a real result, not a forecast. For the retention team, every agent starts the day knowing who to call, why, and what to offer."
**SAY:** "And the cost is low. About 1,600 dollars for a six-week test. About 3,500 dollars a month in production."
**OBJECTION:** "The model results come from the build. The business numbers are our assumptions: 2 million customers, 1.4% churn a month, and 27 euros a month per customer. In week one, we replace them with your real numbers."
**→** "Why do we need this? Because today, you see churn too late."

### Slide 3: Today churn becomes visible only after the customer has left · 2:30–3:15
**SAY:** "Today, the retention team sees churn when the customer asks to move their number. By then it is too late. But the warning signs come earlier, from three places. What the customer says when they call customer care. How the network works for them. And what happens to their bill and their contract. Today nobody puts these signs together. So the team reacts late, the offers are the same for everyone, and analysts wait days for a report. I think your retention team knows this problem well."
**→** "We built a solution with test data, to see what these signs are worth."

### Slide 4: What we learned from the build · 3:15–4:30
**SAY:** "We learned three things. First: customers who talk about switching to a competitor on a call leave at 45%. Everyone else leaves at 10%. That is more than four times higher. Second: if the save desk calls the top 10% of the list, more than half are customers who really want to leave. That is 3.7 times better than calling at random. Third: reading the calls makes the difference. Without the information that AI takes from the calls, the model is clearly worse. So we measured the value of AI. We did not just assume it."
**SAY:** "The best sign is what the customer says on the call. We already have it. We only need to read it."
**SAY:** "For you, as Head of Data Platform: we use a gradient boosting model with 21 features. We tested it on 5,000 customers it had never seen. The score is 0.78 with the call data, and 0.73 without it."
**OBJECTION:** "With real data, I expect lower results. So in the test, our target is 2.5 times, not 3.7."
**→** "How do we build this? Let me show you the architecture. You will see it working in the demo at the end."

---

## Part 2: How it is built (4 minutes, mostly technical)

### Slide 5: One governed journey from raw data to the agent's screen · 4:30–5:45
**SAY:** "Now the architecture, mainly for you, as Head of Data Platform. Lakeflow loads the data and checks its quality. Unity Catalog controls access to everything, and it tracks where the data comes from. AI Functions read the calls. The churn model is tracked in MLflow. Lakebase is the database for the app. Genie uses the same tables. And the app is the agent's screen. We deploy everything together, as code."
**SAY:** "For you, as CCO, this means one platform, one copy of the data, and one set of permissions."

### Slide 6: Security and governance by design · 5:45–6:45
**SAY:** "The call text is the most sensitive data. So it has the strongest protection. It is tagged, hidden, and only the data team can read it. The retention team and Genie see only the results. The AI models run inside Databricks, so no data goes outside."
**OBJECTION:** "We check quality in three ways. First, rules in the pipeline remove bad data. Second, in the build, the AI agreed 95% of the time with the reason the customer chose on the phone menu. Third, in the test, we will compare the AI with 500 calls checked by people. Our target is at least 85%."

### Slide 7: Decisions and trade-offs · 6:45–8:15
**SAY:** "These are the choices we made, and why. We use ready AI functions, not a custom-trained model. This is faster, and everything stays secure. We use a simple model, not deep learning, because the agent needs to know why they are calling. We use Lakebase for the app, because the app needs fast reads and writes. We start with simple rules for the offers. Later, we learn from real results. And we start with a night job. We move to real time only if the pilot shows we need it."
**OBJECTION:** "Delta, Postgres and MLflow are open source. So you are not locked in."
**→** "Now the business. What is it worth, what does it cost, and how do we prove it fast?"

---

## Part 3: Value, cost and plan (4 minutes, business)

### Slide 8: Value, cost and plan
**SAY:** Use the line above and go to the next slide.

### Slide 9: Business case: about €5.0M net per year · 8:15–9:45
**SAY:** "Here is the calculation, step by step. Streamline has 2 million customers. Each month, 1.4% leave. That is about 336,000 customers a year, and about 109 million euros of revenue. We want to keep 20,000 of them. If agents save one customer in four, we need to reach 80,000 customers who want to leave. Our list is right 56% of the time. So we need about 143,000 calls a year. That is about 550 calls a day. 20,000 customers kept, at 324 euros a year each, is 6.5 million euros. The offers cost about 1.4 million euros. The platform costs about 40,000 euros. So the net value is about 5 million euros a year."
**OBJECTION:** "And if the agents save only half as many customers, the value is still about 2.2 million euros a year."

### Slide 10: Cost: about $1.6k for the POC, $3.5k a month in production · 9:45–10:30
**SAY:** "The platform cost is small compared to the value. About 1,600 dollars for the six-week test. About 3,500 dollars a month in production. That is about 42,000 dollars a year. The biggest cost is the AI that reads 690,000 calls a month. If we do the three AI tasks in one step, the cost goes down to about 2,800 dollars a month."
**OBJECTION:** "These are list prices. We will confirm them before any quote."

### Slide 11: Plan: prove it in six weeks, then scale with a control group · 10:30–11:45
**SAY:** "We reduce the risk in three steps. At each step, you decide if we continue, based on your numbers. Step one: a six-week test on your own past data. Our target: the list is 2.5 times better than random, and the AI agrees with people 85% of the time. Step two: a pilot in months 2 and 3. One region, 20 agents, and a control group. We continue if the save rate is at least 5 points better than the control group, and each save costs 80 euros or less. Step three: we roll out from month 4."
**SAY:** "From you, we need four things. A sponsor. A retention lead who owns the offers. One data engineer. And three months of anonymous call data."
**OBJECTION:** "So in six weeks you have a list tested on your data. And in month 2 you see the first real results."
**→** "Before I ask for your decision, let me show you how it works in practice."

---

## Part 4: The live demo (7 minutes)

### Slide 12: A day with the Save Desk · 11:45–12:30
**SAY:** "First, here is what I will show you. At 2 in the morning, the platform reads the calls and gives every customer a risk score. At 8:30, the agent opens the list of customers to call. During the call, the agent saves the result. And at any time, the manager can ask Genie a question. I will show you three things: who to call, why, and what to offer."
**DO:** Go to the simulator tab.

### Demo step 1: Solution overview · 12:30–12:45
**SAY:** "This is Streamline's Databricks workspace. Here you see the full journey, from the raw data to the app. Everything is on one platform."

### Demo step 2: Jobs & Pipelines · 12:45–13:30
**DO:** Click *Jobs & Pipelines* → **▶ Run now**. Then click the tab **Lakeflow pipeline: save-desk-ingest**.
**SAY:** "I start the night job. It loads the data, reads the calls with AI, applies the security rules, scores every customer, and updates the app. Last night it processed 20,000 customers and almost 14,000 calls."
**SAY:** "For you, as Head of Data Platform: we load the data with Lakeflow. It loads only the new files. It also has quality rules. For example, a call without text or a strange bill is removed before it reaches the model."
**OBJECTION:** "In production, the data comes directly from your billing, network and contact centre systems. The rest of the solution does not change."

### Demo step 3: AI Functions · 13:30–14:15
**DO:** Click *AI Functions* → **▶ Run**. Point at the call marked **1 · switching**.
**SAY:** "Now the AI reads every call with simple SQL. For each call, it finds the mood of the customer, the reason for the call, and whether they want to leave. Here, the customer is calling about a bill that almost doubled. The AI marks that they want to switch."
**OBJECTION:** "The AI models run inside Databricks. So the calls never leave the platform. And every night we read only the new calls, so the cost stays low."

### Demo step 4: Catalog · 14:15–14:45
**DO:** Click *Catalog* → **raw › care_calls** → tab **Sample data**. Then click the **Lineage** tab on *save_list*.
**SAY:** "The call text is personal data. I am logged in as a retention user, so Unity Catalog hides the text. I see the word REDACTED. Only the data team can read it. And here we see the full path of the data, from the raw files to the app and Genie."

### Demo step 5: The Save Desk app (the most important part) · 14:45–16:45
**DO:** Click *Apps*.
**SAY:** "This is the agent's screen. It is a Databricks App. At the top, you see 1,825 customers at risk. Together they pay about 838,000 euros a year. The list is sorted by how much money is at risk."
**SAY:** "The first customer has an 89% chance of leaving in the next 60 days. That is 2,377 euros at risk. Why? They talked about switching on a call, and their bill went up by 50%. So the app suggests a loyalty price match. It also gives the agent a first sentence to say." *(Read the first sentence on the screen.)*
**DO:** Click **Offer accepted**.
**SAY:** "With one click, the agent saves the result. Now the counter shows one customer saved."
**DO:** Change the filters: **network** and **South**.
**SAY:** "Now I show only the customers with network problems in the South. A discount does not fix a bad network. So this list goes to the network team too."
**DO:** Set the filters back to *All drivers* and *All regions*.

### Demo step 6: Lakebase · 16:45–17:15
**DO:** Click **view in Lakebase** in the green message.
**SAY:** "Here is the result I just saved. It is in Lakebase, the database behind the app. It was saved in milliseconds. Every week, these results go back to the model. So the model learns which offers really keep customers."

### Demo step 7: Genie · 17:15–18:00
**DO:** Click *Genie* → the sample question **"What is the churn rate for customers who mentioned switching on a care call vs. those who did not?"**
**SAY:** "Last, the manager. With Genie, anyone can ask a question in plain English. I asked: what is the churn rate for customers who talked about switching, compared to the others? The answer: 45% against 10%. Genie also shows the SQL query, so you can check every answer."

### Back to the deck · 18:00–18:30
**DO:** Go back to the deck, on slide 12.
**SAY:** "So what does this mean for you? Today you react when the customer is already gone. With this, you call the customer while you can still keep them. For you, as CCO, 20,000 customers kept means 6.5 million euros a year. For you, as Head of Data Platform, it all runs on one platform with one set of permissions."
**DO:** Go to the next slide (slide 13).

---

## Part 5: The decision (1 minute)

### Slide 13: The decision we are asking for · 18:30–19:30
**SAY:** "To sum up. One point less churn. About 5 million euros a year. One secure platform. And we prove it in six weeks, before you invest more. So I am asking you for three things. Approve a six-week test. Name a sponsor and a retention lead. And share three months of anonymous data. In six weeks, you will know if this list finds your customers who want to leave."
**ASK, then stop talking:** "What do you need to see to approve the test?"

### Slides 14, 15 and 16: only if needed
Slide 14 has the questions we expect. Show it only if they ask a question.
Only if they ask "Did this really run?": "Yes. All the results are saved as text in the code repository: the run logs, the model results and the Genie answers."

---

## Questions and answers: give the answer first, then one reason

**CCO (business)**
| Question | Answer |
|---|---|
| Is it too expensive? | No. The platform costs about 42,000 dollars a year. The value is about 5 million euros. The real cost is the offers, and the control group checks that. |
| How fast do we see value? | In six weeks, a list tested on your data. In month 2, the first real results. |
| It is test data. | Yes. That is why our target in the test is lower: 2.5 times, not 3.7. We measure it on your data before you invest more. |
| Are we just giving discounts? | No. The offer depends on the reason. A network fix costs 15 euros. Only customers who leave because of price get a discount. |
| What if it does not work? | With half the results, it is still worth about 2.2 million euros. If the test fails, we stop after six weeks and about 1,600 dollars. |

**Head of Data Platform (technical)**
| Question | Answer |
|---|---|
| How do we connect our systems? | Lakeflow Connect or Kafka bring data from billing, network and the contact centre. The results are in Postgres, so your CRM can read them. |
| Data quality? | Quality rules in the pipeline. AI results checked against people. Model changes tracked in MLflow. |
| Security and personal data? | The call text is tagged and hidden in Unity Catalog. The AI runs inside Databricks. Users see only the final tables. The app has its own technical user. We track the data from start to end. |
| Why Lakebase and not Delta? | The app needs very fast reads and writes. That is a database job. Lakebase does it. |
| Why not real time? | The team decides once a day, so a night job is cheaper. Real time is step three. |
| AI cost at scale? | About 1,200 dollars a month for 690,000 calls. One combined step cuts it by about 60%. |
| Are we locked in? | No. Delta, Postgres and MLflow are open source. |
| Is this demo live? | It is a demo workspace that shows last night's run on test data. The code in the repository deploys the same solution to a real workspace. |

## Reminders
- Say the structure: "I will show you…", "Now I show it…", "This means for you…"
- Say who you talk to: "For you, as CCO…", "For you, as Head of Data Platform…"
- Read the numbers on the screen out loud.
- The demo is at the end, on slide 12. Just go to the next slide each time.
- Keep the demo to about 7 minutes.
- If you get lost in the demo, open the **Demo script** panel (bottom left) and click the next step.
- Ask the last question, then wait.
