"""FE Bar deck — Streamline Telco Save Desk, on the official Databricks corporate template.
python3 build_deck.py out.pptx
"""
import os, sys
sys.path.insert(0, os.path.expanduser('~/Documents/dsa_render'))
from lib import *

TEMPLATE = os.path.join(ROOT, 'tpl.pptx')
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser('~/Documents/febar_build/out.pptx')
d = Deck(TEMPLATE)
L_CLOSING = 26
LT = 'C9D1D4'


import glob as _g
def icon(slide, name, x, y, size=0.5):
    hits = sorted(_g.glob(os.path.join(ICONS, f'{name}_r2.png'))) or sorted(_g.glob(os.path.join(ICONS, f'{name}_r*.png')))
    return slide.shapes.add_picture(hits[0], I(x), I(y), I(size), I(size))


def P(name):
    """Databricks product name, highlighted (Lava bold)."""
    return (name, dict(bold=True, color=LAVA))


def kpi(s, x, y, w, h, value, label, sub, dark=False, vsize=30):
    card(s, x, y, w, h, fill=NAVY if dark else WHITE)
    shape(s, 'rect', x, y, 0.06, h, fill=LAVA)
    tb(s, x + 0.22, y + 0.12, w - 0.35, 0.3, [[(label, dict(bold=True))]], size=10.5, color=LT if dark else SLATE)
    tb(s, x + 0.22, y + 0.42, w - 0.35, 0.65, [[(value, dict(bold=True))]], size=vsize, color=WHITE if dark else NAVY)
    tb(s, x + 0.22, y + h - 0.5, w - 0.35, 0.42, sub, size=10, color=LT if dark else BODY)


def textcard(s, x, y, w, h, head, lines, dark=False, label=None, size=11.5):
    card(s, x, y, w, h, fill=NAVY if dark else WHITE)
    yy = y + 0.2
    if label:
        tb(s, x + 0.25, yy, w - 0.5, 0.25, [[(label.upper(), dict(bold=True))]], size=9, color=CORAL)
        yy += 0.27
    tb(s, x + 0.25, yy, w - 0.5, 0.35, [[(head, dict(bold=True))]], size=14, color=WHITE if dark else NAVY)
    tb(s, x + 0.25, yy + 0.42, w - 0.5, h - (yy - y) - 0.5, lines, size=size,
       color=WHITE if dark else BODY, bullets=isinstance(lines, list), spacing=5)


# ===================================================================== 1 COVER
s = d.new(Deck.L_COVER, title='Keep the customers who are already telling us they will leave',
          subtitle='Streamline Telco Save Desk  |  Churn early warning on the Databricks Data Intelligence Platform',
          keep=(0, 1, 2, 12))
for ph in s.placeholders:
    i = ph.placeholder_format.idx
    if i == 0:
        ph.left, ph.top, ph.width, ph.height = I(0.83), I(1.6), I(8.6), I(2.4)
        for p in ph.text_frame.paragraphs:
            for r in p.runs: r.font.size = Pt(38)
    if i == 1:
        ph.left, ph.top, ph.width, ph.height = I(0.83), I(4.1), I(9.0), I(0.5)
        for p in ph.text_frame.paragraphs:
            pPr = p._p.get_or_add_pPr(); pPr.set('marL', '0'); pPr.set('indent', '0')
            for r in p.runs: r.font.size = Pt(16); r.font.color.rgb = rgb(CORAL)
    if i == 2:
        set_text(ph.text_frame, 'Databricks account team · proposal for the Chief Customer Officer,\nthe Head of Retention and the Head of Data Platform · October 2026')
tb(s, 0.83, 5.5, 9, 0.3, 'Demo built on synthetic data. Streamline Telco is a fictional company.', size=10, color=LT)
notes(s, """
SETUP (30 s): Thank you for the time. In the next 25 minutes I want to show you how Streamline can keep customers who are already telling you they are about to leave.
Who is in the room: the Chief Customer Officer, who owns churn and the retention budget; the Head of Retention, who runs the save desk; and the Head of Data Platform, who will have to live with what we build.
Agenda: the outcome, what we found, a 6-minute live demo, then architecture, cost and the plan. Please interrupt me at any point.
""")

# ===================================================================== 2 OUTCOME
s = d.new(Deck.L_CONTENT, title='The outcome: one point less churn, €5M a year kept',
          subtitle='What we propose, what it is worth and what it costs')
k = [('16.8% → 15.8%', 'Annual churn target', '−1.0 point in year one', True),
     ('20,000', 'Subscribers kept per year', 'out of ~336,000 who leave today', False),
     ('€6.5M', 'Revenue protected per year', '€5.0M net of offers and platform', False),
     ('6 weeks', 'Time to first value', 'POC ≈ $1.6k compute · run ≈ $3.5k / month', False)]
for i, (v, l, sub, dk) in enumerate(k):
    kpi(s, 0.82 + i * 2.95, 1.95, 2.8, 1.75, v, l, sub, dark=dk, vsize=21 if i == 0 else 30)
textcard(s, 0.82, 3.95, 5.75, 2.2, 'For the Chief Customer Officer',
         ['Churn falls and revenue stays, with a number you can track every month',
          'Every save is logged and compared with a control group, so the result is measured'])
textcard(s, 6.72, 3.95, 5.78, 2.2, 'For the Head of Retention',
         ['Agents start each day with a ranked list: who to call, why, and what to offer',
          "Calling the model's top 10% reaches 3.7× more real churners than random outreach"])
source(s, 'Business figures are planning assumptions for Streamline (slide 10). Model figures are measured on the synthetic-data build (evidence/model_metrics.json).')
notes(s, """
TELL: Let me lead with the outcome. Our target is one point of annual churn: from 16.8% to 15.8%. For Streamline that is 20,000 customers a year who stay, about 6.5 million euros of revenue protected, or about 5 million net after the cost of offers and the platform.
For you as CCO, it is one number tracked monthly against a control group, not a forecast. For retention, it means every agent starts the day knowing who to call, why, and what to offer.
Cost: about 1.6 thousand dollars of compute for a 6-week POC, about 3.5 thousand dollars a month in production at list price.
""")

# ===================================================================== 3 PROBLEM
s = d.new(Deck.L_CONTENT, title='Today churn becomes visible only after the customer has left',
          subtitle='The signals already exist, but they sit in three systems that nobody joins up')
cols = [('s77_Mobile_Device', 'Care calls', 'Customers say it out loud',
         '"Match it or I am porting my number out." Stored as recordings and transcripts, never read at scale.'),
        ('s77_Network_Data_Sources', 'Network', 'Experience degrades first',
         'Dropped calls and slow data appear weeks before the porting request, but stay with the network team.'),
        ('s75_Dollars___Expense', 'Billing and contract', 'Bill shock, contract end',
         'A bill increase or a contract ending within 60 days opens the door to a competitor offer.')]
for i, (ic, lab, h, t) in enumerate(cols):
    x = 0.82 + i * 3.93
    card(s, x, 1.95, 3.78, 1.95)
    icon(s, ic, x + 0.25, 2.12, 0.5)
    tb(s, x + 0.9, 2.12, 2.7, 0.25, [[(lab.upper(), dict(bold=True))]], size=9, color=CORAL)
    tb(s, x + 0.9, 2.36, 2.75, 0.35, [[(h, dict(bold=True))]], size=13.5, color=NAVY)
    tb(s, x + 0.25, 2.85, 3.3, 1.0, t, size=11, color=BODY)
textcard(s, 0.82, 4.15, 5.75, 2.25, 'Today',
         ['Retention reacts to the porting request, when the decision is already made',
          'Offers are generic and go to whoever calls', 'Analysts wait days for BI tickets on "where and why"'])
textcard(s, 6.72, 4.15, 5.78, 2.25, 'With the Save Desk',
         ['Every subscriber scored nightly, the riskiest and most valuable first',
          'The offer matches the reason: network fix, price match or early renewal',
          'Managers ask Genie in plain English and get the answer in seconds'], dark=True)
notes(s, """
TELL: Today churn is visible only once the porting request arrives, and by then the decision is made.
The signals exist earlier, in three places: what customers say on care calls, how the network performs for them, and what happens to their bill and contract. Nobody joins them up, so the retention team waits, offers are generic, and analysts wait for BI tickets.
PAUSE and ask the CCO: does this match what you see? How do you find at-risk customers today?
""")

# ===================================================================== 4 FINDINGS
s = d.new(Deck.L_CONTENT, title='What we learned from the build',
          subtitle='Results on 20,000 synthetic subscribers and 13,749 care calls, committed as run output in the repository')
k = [('45.2%', 'Churn after a switching mention', 'vs 10.4% for everyone else: 4.3× higher'),
     ('56%', 'Precision of the top-10% list', '3.7× the 15.1% base rate'),
     ('+0.053', 'Value of reading calls with Gen AI', 'ROC-AUC 0.729 → 0.783 · top-10% precision 42% → 56%'),
     ('39 / 37 / 24%', 'Main reason for at-risk customers', 'price / network / contract')]
for i, (v, l, sub) in enumerate(k):
    kpi(s, 0.82 + i * 2.95, 1.95, 2.8, 1.85, v, l, sub, vsize=26 if i == 3 else 30)
key_message(s, 'The strongest single predictor is what the customer says on the care call. That signal is free; we only need to read it.')
tb(s, 0.82, 4.15, 11.6, 1.6,
   [[('How we measured it: ', dict(bold=True, color=NAVY)), ('a gradient-boosting model with 21 features, tracked in ', {}), P('MLflow'),
     (', tested on a 25% hold-out. To isolate the value of Gen AI we retrained the same model without the features that ', {}),
     P('AI Functions'), (' extract from care calls (an ablation). Switching intent is the #1 feature (importance 0.31).', {})]],
   size=13, color=BODY)
source(s, 'Source: evidence/model_metrics.json, evidence/model_run_output.txt, evidence/query_results.md (synthetic data, seed 42).')
notes(s, """
TELL: Three things stood out in the build.
One: customers who mention switching on a care call churn at 45%, versus 10% for everyone else. More than four times higher.
Two: if the save desk calls the model's top 10%, more than half are real churners, 3.7 times better than calling at random.
Three: reading the calls is what makes the difference. When we remove the Gen AI call features, the model gets clearly worse. The value of Gen AI here is measured, not assumed.
FOR THE TECHNICAL STAKEHOLDER: hold-out test set of 5,000 subscribers; PR-AUC 0.49; precision 0.66 at the 0.5 threshold. On real data we expect lower absolute numbers, so the POC gate is 2.5× lift, not 3.7×.
""")

# ===================================================================== 5 DAY IN THE LIFE / DEMO
s = d.new(Deck.L_CONTENT, title='A day with the Save Desk',
          subtitle='What changes for the people who own the outcome, and what the demo shows')
steps = [('02:00', 'The platform does the reading', 'New bills, network data and yesterday\'s calls are ingested; AI reads every call; every subscriber gets a fresh score.'),
         ('08:30', 'The agent opens the save list', 'Ranked by value at risk, with the top three reasons, the next best offer and a suggested opening line.'),
         ('On the call', 'Log the outcome', 'Accepted, declined or call back: one click, saved in milliseconds, used in next week\'s retraining.'),
         ('Anytime', 'The manager asks Genie', '"Which region has the most at-risk subscribers because of network problems?" The answer comes with its SQL.')]
for i, (t, h, b) in enumerate(steps):
    y = 1.95 + i * 1.12
    shape(s, 'oval', 0.82, y + 0.05, 0.5, 0.5, fill=LAVA, text=[[(str(i + 1), dict(bold=True))]], size=14, color=WHITE)
    tb(s, 1.5, y, 5.0, 0.3, [[(t + '  ·  ', dict(bold=True, color=CORAL)), (h, dict(bold=True))]], size=13.5, color=NAVY)
    tb(s, 1.5, y + 0.33, 5.0, 0.75, b, size=11, color=BODY)
card(s, 6.85, 1.95, 5.65, 4.45, fill=NAVY)
tb(s, 7.1, 2.12, 5.2, 0.3, [[('LIVE DEMO · ABOUT 6 MINUTES', dict(bold=True))]], size=9.5, color=CORAL)
tb(s, 7.1, 2.42, 5.2, 0.4, [[('Tell, show, tell', dict(bold=True))]], size=16, color=WHITE)
tb(s, 7.1, 2.95, 5.2, 3.3, [
    [('Tell: ', dict(bold=True)), ("the retention team's morning, in their words", {})],
    [('Show: ', dict(bold=True)), ('the top subscriber: 89% risk, €2.4k at stake, bill up 50%, mentioned switching. Offer: loyalty price match. Log "accepted".', {})],
    [('Show: ', dict(bold=True)), ('filter to network-driven risk in the South, the list for the network team', {})],
    [('Show: ', dict(bold=True)), ('ask Genie the switching question: 45% vs 10%', {})],
    [('Tell: ', dict(bold=True)), ('what it means for churn, revenue and cost per save', {})]],
   size=11.5, color=WHITE, bullets=True, spacing=6)
notes(s, """
TELL (before the demo): I'll show you the Save Desk the way an agent and a manager would use it. Three things to look for: who to call, why, and what to offer.
SHOW (app/demo.html):
1. Save list tab: KPI strip, 1,825 at-risk subscribers, 838k euros of annual revenue at risk in this sample. The list is ranked by value at risk, not by probability alone.
2. Open STL102197: 89% churn probability, 2,377 euros at risk. Why: mentioned switching on a care call, bill up 50%. Offer: loyalty price match. Read the suggested opening line. Click "Offer accepted": saved to Lakebase, counter updates.
3. Filter driver = network, region = South: this list goes to the network team, because a discount will not fix a dropped call.
4. Ask Genie tab: the switching question returns 45.2% vs 10.4%, with the SQL shown so the answer can be checked.
TELL (after): what you saw is the difference between reacting to a porting request and calling a customer while there is still time. At 20,000 saves a year that is 6.5 million euros of revenue.
""")

# ===================================================================== 6 ARCHITECTURE
s = d.new(Deck.L_CONTENT, title='One governed journey from raw data to the agent\'s screen',
          subtitle='Every stage runs on the Databricks Data Intelligence Platform and deploys as one Databricks Asset Bundle')
flow = [('s82_Output', 'Raw data', None, 'Billing, network probes, contracts, care-call transcripts'),
        ('s57_Data_Pipelines', 'Ingest', 'Lakeflow', 'Declarative pipeline, Auto Loader, data-quality expectations'),
        ('s75_GDPR', 'Govern', 'Unity Catalog', 'Medallion schemas, tags, column mask, grants, lineage'),
        ('s57_Full_Lifecycle_ML', 'Intelligence', 'AI Functions · MLflow', 'Sentiment, intent, switch intent; churn model in UC'),
        ('s81_Delta_Table', 'Serve', 'Lakebase', 'Save list synced to Postgres; outcomes written back'),
        ('s57_Business_Insights', 'Ask', 'Genie', 'Plain-English questions on the same gold tables'),
        ('s73_Apps_Services', 'Act', 'Databricks Apps', 'Save Desk for agents and managers')]
W = 1.6; G = 0.07
for i, (ic, h, prod, b) in enumerate(flow):
    x = 0.82 + i * (W + G)
    card(s, x, 1.95, W, 2.35, fill=NAVY if i == 0 else WHITE)
    icon(s, ic, x + 0.18, 2.1, 0.42)
    tb(s, x + 0.15, 2.6, W - 0.25, 0.3, [[(h, dict(bold=True))]], size=12, color=WHITE if i == 0 else NAVY)
    if prod:
        tb(s, x + 0.15, 2.9, W - 0.25, 0.4, [[P(prod)]], size=10.5)
    tb(s, x + 0.15, 3.32, W - 0.25, 0.95, b, size=9.5, color=LT if i == 0 else BODY)
three = [('Integrated, not stitched', [('The app reads ', {}), P('Lakebase'), (', synced from the gold table the model writes, built from the calls AI enriched. One lineage graph in ', {}), P('Unity Catalog'), ('.', {})]),
         ('Closed loop', [('Outcomes logged in the app return to the lakehouse. The model learns which offers actually save which customers.', {})]),
         ('Production path', [('Synthetic files are replaced by ', {}), P('Lakeflow Connect'), (' or Kafka feeds from billing, network and the contact-centre platform. Nothing downstream changes.', {})])]
for i, (h, runs) in enumerate(three):
    x = 0.82 + i * 3.93
    card(s, x, 4.55, 3.78, 1.85)
    tb(s, x + 0.25, 4.72, 3.3, 0.3, [[(h, dict(bold=True))]], size=13, color=NAVY)
    tb(s, x + 0.25, 5.07, 3.35, 1.3, [runs], size=10.5, color=BODY)
notes(s, """
FOR THE TECHNICAL STAKEHOLDER: one journey, all on Databricks.
Lakeflow Declarative Pipelines ingest with Auto Loader and enforce expectations. Unity Catalog governs everything: medallion schemas, a tag and a column mask on transcripts, gold-only grants, automatic lineage.
AI Functions (ai_analyze_sentiment, ai_classify, ai_query) read every call from SQL; the churn model is scikit-learn tracked in MLflow and registered in Unity Catalog.
The scored save list is synced to Lakebase, managed Postgres, for millisecond reads and transactional write-back from the app. Genie answers questions on the same gold tables. The Databricks App is the agent's screen.
The whole thing deploys as one Asset Bundle: a pipeline, a nightly job, a Lakebase instance and an app.
FOR THE BUSINESS STAKEHOLDER (one line): one platform, one copy of the data, one set of permissions.
""")

# ===================================================================== 7 SECURITY
s = d.new(Deck.L_CONTENT, title='Security and governance by design',
          subtitle='Transcripts are the sensitive asset, so they get the strictest controls')
textcard(s, 0.82, 1.95, 5.75, 4.45, 'Data never leaves the governed platform', [
    [P('AI Functions'), (' call Databricks-hosted models; transcripts are not sent to a third-party API', {})],
    [('Raw transcripts are tagged sensitive and masked by a ', {}), P('Unity Catalog'), (' column mask. Only the data team sees the text.', {})],
    [('The retention team and ', {}), P('Genie'), (' read gold tables only', {})],
    [P('Lakebase'), (' uses the same workspace identity; the app runs as its own service principal', {})]], label='Security')
textcard(s, 6.72, 1.95, 5.78, 4.45, 'Quality and trust', [
    [P('Lakeflow'), (' expectations drop or flag bad rows (e.g. an implausible bill) before they reach the model', {})],
    [('LLM intent agrees with the IVR queue on 95% of calls. The POC adds a check against 500 calls labelled by people.', {})],
    [('Every score carries its top three reasons, so agents can trust and explain it', {})],
    [P('Genie'), (' shows the SQL behind every answer; trusted queries are curated', {})]], label='Data quality')
notes(s, """
FOR THE TECHNICAL STAKEHOLDER: the sensitive asset is the transcript text, so it gets the strictest controls: a tag, a column mask, and access only for the data team. Retention users and Genie only see gold tables with derived signals, never the raw text.
The LLM runs on Databricks-hosted models through AI Functions, so the data does not go to an outside API.
Data quality: pipeline expectations, a 95% agreement between LLM intent and the IVR queue in the build, and in the POC a test against 500 calls labelled by people, with a target of at least 85%.
""")

# ===================================================================== 8 DECISIONS
s = d.new(Deck.L_CONTENT, title='Decisions and trade-offs',
          subtitle='Why this design, and what we deliberately did not do')
rows = [['Decision', 'Why', 'Trade-off we accept'],
        [[P('AI Functions'), (' in SQL, not a fine-tuned model', {})], 'Short transcripts, generic task; ships in days with no model to host', 'Per-token cost at scale. We process only new calls and can move to one combined prompt (about −60% tokens).'],
        ['Gradient boosting, not deep learning', 'Tabular data; agents need the "why"; retrains in minutes', 'A more complex model might gain some AUC but lose explainability'],
        [[P('Lakebase'), (' for the app, not Delta reads', {})], 'Point lookups and write-back are transactional work that needs millisecond reads', 'A second store, kept in sync declaratively by a synced table'],
        ['Rule-based next best offer first', 'Retention owns the offer catalogue; rules are easy to audit', 'Not optimised yet. Logged outcomes later train an uplift model.'],
        ['Nightly batch scoring, not real time', 'Save decisions are daily; batch cuts cost and complexity', 'Same-day signals wait until the next run. Real time is a phase-3 option.']]
table(s, 0.82, 1.95, 11.68, 4.3, rows, col_w=[3.2, 4.0, 4.48], header_fill=NAVY, size=11, header_size=11.5, row_h=0.7)
notes(s, """
FOR THE TECHNICAL STAKEHOLDER: these are the choices I would defend.
AI Functions, not a fine-tune: the task is generic, so we ship fast and keep everything governed. The cost is per token, managed by processing only new calls and combining the three prompts into one.
Gradient boosting: explainability matters more than the last point of AUC, because agents have to say why they are calling.
Lakebase: the app does lookups and writes, which is OLTP work; Delta is for analytics.
Rules for offers first, then an uplift model trained on real outcomes. Batch first, real time later if the pilot shows that same-day signals matter.
""")

# ===================================================================== 9 DIVIDER
s = d.new(Deck.L_SECTION, title='Value, cost and plan')
notes(s, 'TRANSITION: So what is it worth, what does it cost, and how do we prove it quickly?')

# ===================================================================== 10 BUSINESS CASE
s = d.new(Deck.L_CONTENT, title='Business case: about €5.0M net per year',
          subtitle='Conservative planning assumptions, replaced by Streamline actuals in week 1 of the POC')
a = [['Assumption', 'Value'], ['Postpaid subscribers', '2,000,000'], ['Monthly churn (annual)', '1.4% (16.8%)'],
     ['Subscribers lost per year', '336,000'], ['Average revenue per subscriber', '€27 / month'],
     ['Revenue lost to churn per year', '€108.9M'], ['Precision of top-10% list (build)', '56%'],
     ['Save rate on reached churners', '25%'], ['Average offer cost (offer mix)', '€40']]
b = [['Year-one result', 'Value'], ['Subscribers saved (−1.0 pt churn)', '20,000'], ['Churners to reach (20,000 ÷ 25%)', '80,000'],
     ['Calls to make (80,000 ÷ 56%)', '≈143,000 (≈550 / day)'], ['Revenue protected (20,000 × €324)', '€6.48M'],
     ['Offer cost (≈35,600 accepted × €40)', '−€1.42M'], ['Platform run cost (slide 11)', '−€0.04M'],
     ['Net benefit per year', '≈ €5.0M'], ['Cost per save', '≈ €73']]
table(s, 0.82, 1.95, 5.75, 3.9, a, col_w=[3.75, 2.0], header_fill=NAVY, size=11, row_h=0.43, align='lr')
table(s, 6.72, 1.95, 5.78, 3.9, b, col_w=[3.48, 2.3], header_fill=NAVY, size=11, row_h=0.43, align='lr')
source(s, 'Accepted offers = 20,000 saves + 25% of ≈62,600 contacted non-churners. Revenue view; margin view built with Finance in the POC. Streamline Telco is fictional; all business figures are illustrative.', y=6.2)
notes(s, """
FOR THE CCO: the math is simple and I want you to challenge every input.
2 million postpaid subscribers, 1.4% monthly churn, so about 336,000 leave a year, about 109 million euros of revenue.
To save 20,000 we need to reach 80,000 churners at a 25% save rate. With 56% precision that is about 143,000 calls a year, around 550 a day for the save desk.
20,000 saves at 324 euros a year is 6.5 million. Offers cost about 1.4 million, because some go to customers who would have stayed. The platform costs about 40 thousand. Net: about 5 million euros a year, 73 euros per save.
DOWNSIDE: if the save rate is half, 12.5%, the same calls still give about 2.2 million net.
""")

# ===================================================================== 11 COSTS
s = d.new(Deck.L_CONTENT, title='Cost: about $1.6k for the POC, $3.5k a month in production',
          subtitle='Databricks list-price estimates (AWS, pay-as-you-go), confirmed with a Lakemeter sizing before any quote')
c = [['Component', 'POC · 6 weeks · 200k subscribers', 'POC', 'Production · 2M subscribers', 'Per month'],
     [[P('AI Functions'), (' on care calls', {})], '200k-call backfill + re-runs', '$400', '~690k calls, 3 AI functions per call', '$1,170'],
     [[P('Lakeflow'), (' pipeline', {})], '~150 DBU serverless', '$60', 'Nightly incremental, ~600 DBU', '$240'],
     [[P('MLflow'), (' training + scoring', {})], '~200 DBU serverless', '$80', 'Nightly scoring + weekly retrain, ~300 DBU', '$120'],
     [[P('SQL warehouse'), (' (Genie, SQL)', {})], 'Small, ~3 h per working day', '$760', 'Small, ~4 h / working day + 1 h nightly', '$990'],
     [[P('Lakebase'), {}] if False else [P('Lakebase')], '1 CU, working hours', '$150', '2 CU, always on', '$730'],
     [[P('Databricks Apps')], 'Working hours (~300 h)', '$105', 'Always on', '$255'],
     ['Cloud storage', '< 100 GB', '$5', '~1 TB', '$25'],
     ['Total', '', '≈ $1,560', '≈ $42k per year', '≈ $3,530']]
table(s, 0.82, 1.95, 11.68, 3.7, c, col_w=[2.6, 3.0, 1.05, 3.6, 1.43], header_fill=NAVY, size=10.5, row_h=0.4, align='llrlr')
tb(s, 0.82, 5.82, 11.68, 0.9,
   'Unit prices: Foundation Model API, Llama 3.3 70B, $0.50 per 1M input and $1.50 per 1M output tokens (read on databricks.com/product/pricing/foundation-model-serving). '
   'Estimates to validate: serverless jobs and pipelines $0.40/DBU · serverless SQL $0.70/DBU (Small = 12 DBU/h) · Lakebase $0.50/DBU with 1 CU ≈ 1 DBU/h · App 0.5 DBU/h at $0.70. '
   'One combined AI prompt instead of three cuts production to about $2.8k a month.', size=9.5, color=SLATE)
notes(s, """
FOR BOTH: the platform cost is small compared with the value. About 1.6 thousand dollars of compute for the POC, about 3.5 thousand a month in production at list price, about 42 thousand a year.
The biggest line is Gen AI on 690,000 calls a month. If we combine the three AI calls into one prompt, the total drops to about 2.8 thousand a month.
HONESTY: only the Foundation Model API rate is read directly from the public pricing page; the others are list-price estimates that the account team confirms with a Lakemeter sizing before any quote.
""")

# ===================================================================== 12 PLAN
s = d.new(Deck.L_CONTENT, title='Plan: prove it in six weeks, then scale with a control group',
          subtitle="Each phase has a go/no-go measured in the retention team's own KPIs")
textcard(s, 0.82, 1.95, 3.78, 3.0, 'Prove the signal on real history', [
    '200k subscribers and 3 months of calls in a Streamline workspace', 'Back-test: top-10% precision ≥ 2.5× base rate',
    'AI switch intent ≥ 85% agreement with 500 calls labelled by people', 'Save Desk live for 10 agents'], label='Weeks 1–6 · POC', size=10.5)
textcard(s, 4.75, 1.95, 3.78, 3.0, 'Prove the saves', [
    'One region, 20 agents, a randomised control group', 'Go if the save rate beats control by ≥ 5 points at ≤ €80 per save',
    'Production feeds via Lakeflow Connect'], label='Months 2–3 · pilot', size=10.5)
textcard(s, 8.68, 1.95, 3.82, 3.0, 'All regions, closed loop', [
    'Every agent, nightly scores, weekly retraining on outcomes', 'The network team gets its own at-risk list',
    'Next: uplift model for offers, real-time scoring'], label='Month 4+ · scale', dark=True, size=10.5)
textcard(s, 0.82, 5.15, 11.68, 1.25, 'What we need from Streamline',
         'An executive sponsor in the Customer Office · a retention lead who owns the offer catalogue and the KPI · one data engineer for the source feeds · approval to use 3 months of anonymised care-call transcripts in the POC workspace.', size=11)
notes(s, """
FOR THE CCO: we de-risk in three steps, each with a go/no-go in your KPIs.
POC, 6 weeks: prove the signal on your history. Gate: 2.5× lift and 85% agreement with people's labels.
Pilot, months 2 to 3: prove the saves against a randomised control group in one region. Gate: 5 points better save rate at 80 euros or less per save.
Scale from month 4.
What we need: a sponsor, a retention lead, one data engineer, and approval to use anonymised transcripts.
""")

# ===================================================================== 13 OBJECTIONS
s = d.new(Deck.L_CONTENT, title='Questions we expect, and our answers',
          subtitle='Business and technical concerns')
textcard(s, 0.82, 1.95, 5.75, 4.45, 'Business', [
    [('Discounts for people who would stay? ', dict(bold=True)), ('Some, and it is priced in (€1.42M). The control group measures the real gain; a network fix costs €15, not a discount.', {})],
    [('How fast is the value? ', dict(bold=True)), ('A back-tested list in 6 weeks; first measured saves in month 2.', {})],
    [('What if the numbers are lower? ', dict(bold=True)), ('At half the save rate, net benefit is still ≈ €2.2M a year against ≈ $42k platform cost.', {})]], size=11)
textcard(s, 6.72, 1.95, 5.78, 4.45, 'Technical', [
    [('Integration? ', dict(bold=True)), P('Lakeflow Connect'), (' or Kafka from billing, network and contact centre; outcomes in Postgres, readable by the CRM.', {})],
    [('Data quality? ', dict(bold=True)), ('Pipeline expectations, LLM labels checked against people, drift tracked in ', {}), P('MLflow'), ('.', {})],
    [('Security? ', dict(bold=True)), P('Unity Catalog'), (' masks, grants and lineage; Databricks-hosted models; app service principal.', {})],
    [('Lock-in? ', dict(bold=True)), ('Delta and Postgres are open formats; the model is standard scikit-learn in MLflow.', {})]], size=11)
notes(s, """
Use this slide only if questions come up. Answer at the altitude of whoever asked: outcome and risk for the CCO, mechanism and controls for the platform lead.
COST pushback: the platform is about 42 thousand a year against about 5 million net; the bigger cost is offers, which the control group keeps honest.
TIME pushback: 6 weeks to the first back-tested list.
RISK pushback: the gates are in your KPIs; if the POC does not reach 2.5× lift on your data, we stop.
""")

# ===================================================================== 14 ASK
s = d.new(Deck.L_CONTENT, title='The decision we are asking for',
          subtitle='Approve a six-week POC and name its owners')
kpi(s, 0.82, 1.95, 3.78, 1.9, '6 weeks', 'Time to a back-tested save list', "on Streamline's own data")
kpi(s, 4.75, 1.95, 3.78, 1.9, '≈ $1.6k', 'Platform compute for the POC', 'list-price estimate')
kpi(s, 8.68, 1.95, 3.82, 1.9, '€5.0M', 'Net annual benefit at −1 pt churn', 'measured against a control group', dark=True)
textcard(s, 0.82, 4.15, 11.68, 1.9, 'Next steps', [
    'Confirm the executive sponsor and the retention lead',
    'Share 3 months of anonymised data in a Streamline Databricks workspace',
    'Kick-off workshop: agree the KPI baseline, the control group and the offer catalogue'])
notes(s, """
CLOSE: the ask is simple. Approve a 6-week POC, name a sponsor and a retention lead, and share 3 months of anonymised data.
In 6 weeks you will know, on your own data, whether this list finds your churners. If it does, the pilot proves the saves.
Then STOP TALKING and ask: what would you need to see to approve the POC?
""")

# ===================================================================== 15 APPENDIX
s = d.new(Deck.L_CONTENT, title='Appendix: build evidence and references',
          subtitle='Everything below is committed in the repository as text')
textcard(s, 0.82, 1.95, 5.75, 4.45, 'Run evidence', [
    'evidence/model_run_output.txt: full pipeline log (silver → Gen AI → features → model → save list → serving → Genie)',
    'evidence/model_metrics.json: ROC-AUC 0.783, PR-AUC 0.486, top-10% precision 0.562, ablation 0.729',
    'evidence/query_results.md: five Genie questions with SQL and answers',
    'data/output/*_sample.csv: raw and gold samples; app/demo_data.js: the app data'], size=10.5)
textcard(s, 6.72, 1.95, 5.78, 4.45, 'References', [
    'Foundation Model API pricing: databricks.com/product/pricing/foundation-model-serving',
    'Databricks pricing: databricks.com/product/pricing',
    'AI Functions: docs.databricks.com/aws/en/large-language-models/ai-functions',
    'Lakebase synced tables: docs.databricks.com/aws/en/oltp/projects/sync-tables',
    'Genie: docs.databricks.com/aws/en/genie'], size=10.5)
notes(s, 'Reference only. All URLs checked (HTTP 200) on 28 Oct 2026.')

# ===================================================================== CLOSING
s = d.new(L_CLOSING)
d.save(OUT)
print('saved', OUT, len(d.prs.slides), 'slides')
