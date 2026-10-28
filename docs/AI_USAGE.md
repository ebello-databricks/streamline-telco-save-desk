# AI as a force multiplier

**Tool:** Claude Code (CLI), used as a pair-programmer over one working session, plus a sub-agent to look up Databricks list prices on the public pricing pages.

## Workflow
1. **Framing (me):** picked telecom postpaid churn for a role-play customer (Streamline Telco). Thesis: the care call already contains the churn signal. Chose the buyer (Chief Customer Officer) and the domain owner (Head of Retention), and their KPIs: churn %, saves, cost per save.
2. **Data design (me + AI):** I set the drivers (network degradation, bill shock, commitment end, switching language, tenure, acquisition channel). AI wrote the generator so churn is learnable from them.
3. **Pipeline (AI-drafted, I reviewed):** silver rules, Gen AI enrichment, features, model, save list, serving, Genie questions, app export, all as one script that writes text evidence.
4. **Iteration (me):** reviewing the first app render, I saw the "driver" label contradict the reasons shown to the agent (a subscriber marked *network* whose reasons were bill shock). I changed the driver logic to follow hard signals first and added missing reasons (retention-line calls, tenure, acquisition channel), then re-ran.
5. **Ablation (me):** asked for a model without the Gen AI features to *measure* the value of reading calls (+0.053 AUC) instead of claiming it.
6. **Costing (AI research, I checked):** the sub-agent could verify only the Foundation Model API rate on the pricing pages. I labelled every other rate as an estimate to validate in Lakemeter instead of presenting it as fact.
7. **Deck and demo (AI-drafted, I edited):** the deck is generated with python-pptx on the official Databricks corporate template (`deck/build_deck.py`, with speaker notes as the talk track) and exported to a text-selectable PDF, because the evaluator reads text. The demo is a static click-through twin of the Streamlit app (`app/demo.html`), running on the real gold output.

## Prompts and patterns that worked
- "Make churn learnable from these drivers, then prove it with an ablation."
- "Commit execution output as text; never rely on screenshots."
- "Every number in the deck must trace to `evidence/` or to a labelled assumption."
