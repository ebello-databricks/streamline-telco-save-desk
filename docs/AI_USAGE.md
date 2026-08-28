# AI usage — force multiplier, not autopilot

Built with **Claude Code**. The FE Bar encourages using AI tools; the line is that
the decisions, trade-offs, and narrative are mine. This documents both.

## What I decided (the substance)
- **Use case selection** — chose the Plenitude speech-to-text → churn use case from
  my delivered UCO portfolio because it's the one true end-to-end GenAI+ML journey
  in a clear industry (retail energy).
- **The thesis** — that contact-centre voice is an under-used leading churn
  indicator, and the build should prove voice features out-predict billing alone.
- **Data design** — how churn is generated (latent risk driven by bill shock,
  retention calls, switch-intent mentions, contract expiry, tenure, tariff type)
  so the model recovers real, explainable structure.
- **The feature set, the model choice, the serving pattern, and the value framing**
  (12%→11%, €4.5M) — see `docs/DECISIONS.md`.

## What AI accelerated (the execution)
- Scaffolding the synthetic data generator, the local pipeline, and the six
  workspace notebooks from my specs.
- Writing the Streamlit cockpit, the Asset Bundle, the Genie config, and the
  Lakeview dashboard JSON.
- Building the HTML deck from my existing deck's design system.

## Tools & patterns
- **Claude Code** for the build; the `ai_query` / `ai_analyze_sentiment` /
  `ai_classify` Foundation Model API functions inside the build itself.
- Everything is reproducible: seeded data (`SEED=42`), a one-command local run,
  and committed evidence — so the work can be re-verified, not just trusted.

> If this build is ever flagged for review, the conversation ID of this Claude Code
> session can be provided per the submission form's help link.
