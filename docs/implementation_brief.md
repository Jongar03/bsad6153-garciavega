# Implementation brief: choosing football matches to analyze

Jonathan Garcia Vega | Updated 16 November 2026 | Funding recommendation: build a small SQL dashboard first; fund AI only if it adds measurable value.

## 1. My workflow

I decide which match deserves analysis before considering a bet, including skipping it. My [Milestone 1 log](baseline_log.md) records one review per logged day: October 29–31 and October 1–5; the date ordering needs confirmation. I open apps such as ESPN, OneFootball, and Sofascore, inspect results, compare teams manually, seek missing context, and choose a match.

Recorded times are **12, 10, 8, 3, 5, 7, 2, and 4 minutes**: mean **6.4**, median **6**. Five live entries average **7.2 minutes**; three are reconstructed. Switching sources and finding head-to-head history, home/away performance, and recent goals create friction. These interpretations come from entries and the proposal; the log's frustration prompts remain blank.

## 2. Should this use AI?

Costs below are planning estimates, not measured development effort.

| Option | What it solves | Cost | What could go wrong |
|---|---|---|---|
| A. Checklist and existing spreadsheet | Standardize home/away, recent goals, dates, and a skip rule. | $0 new software; 1–2 setup hours; manual entry each review. | Copying errors, stale figures, continued app switching. |
| B. SQL dashboard | Reuse verified queries for head-to-head results, goals, and home/away rates with denominators and dates. | Free-tier stack; estimated 8–12 build hours plus upkeep. | Bad joins, unequal windows, failed syncs, or historical results mistaken for current form. |
| C. LLM chatbot and bounded agent | M5: explain retrieved evidence and limitations in plain language; M6: draft a weekly shortlist using approved ranking rules. | B plus 6–10 estimated hours for integration/evaluation; API estimate below. | Invented explanations, prompt injection, misleading rankings, and runaway calls. |

**Most value comes from B.** SQL calculates statistics/rankings; scheduled code syncs data. No core decision requires an LLM; its benefit is flexible questions and readable summaries. Evidence covers **760 Premier League matches, 23 teams, 2023/2024 seasons** ([question log](question_log.md)). Current fixtures, five-league coverage, injuries, odds, and calibrated betting probabilities remain unverified; AI cannot supply missing evidence.

## 3. Value hypothesis

**Target:** reduce mean review time from **7.2 minutes (five live entries) to at most 4 minutes**, preserving required evidence. In M4, time ten real sessions in the [usage log](usage_log.md), including loading, verification, and corrections; record missing information, confidence, and usefulness. Compare similar questions and report failures. In M5, compare dashboard-only and AI-assisted sessions; retain AI only if it saves additional time without unsupported claims. Historical tasks cannot demonstrate current-match selection improvements or profitability.

## 4. Early cost estimate

USD estimates, checked 15 November 2026. [Supabase Free](https://supabase.com/pricing): **$0/month**, within 500 MB database/5 GB egress; [GitHub Actions](https://docs.github.com/en/billing/concepts/product-billing/github-actions): **$0** with standard runners in a public repository; [Render Free](https://render.com/docs/free): **$0**, within quotas, with idle sleeping. [API-Football Free](https://www.api-football.com/pricing): **$0**, up to 100 requests/day with season restrictions; budget at most 80/day. Use the provided site address; domain purchases and labor are excluded. Do not auto-upgrade paid services.

Both [OpenAI pricing](https://developers.openai.com/api/docs/pricing) and [Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing) were reviewed. Plan for **Claude Haiku 5.5**, standard short-context rates of **$0.10/million input and $0.50/million output tokens**. At 20 questions/day × 30 days, each totaling 3,000 input + 1,000 output tokens across calls, cost is **$0.0008/question; $0.48/month**. Four weekly summaries at the same allowance add under $0.01; budget **$2/month** including testing/retries, excluding tax. No paid search tools or caching discounts assumed.

Before M5, buy **$20 prepaid API credit, auto-reload off**, with no further purchase without my approval ([billing](https://support.claude.com/en/articles/8977456-how-do-i-pay-for-my-claude-api-usage)). ChatGPT Plus/Claude Pro subscriptions do not pay this app's API calls. Implement a persistent, atomic budget ledger reserving maximum call cost before execution, with a **$19 stop threshold** and $1 buffer; cap tokens and retries. At the threshold or provider credit exhaustion, stop chatbot/agent calls and display “AI budget exhausted”; SQL views remain available. These controls are planned, not configured. M5 will replace estimates with provider-reported token and dollar totals.

## 5. Risks and governance

Wrong summaries could waste my time or mislead public visitors into losing money on bets. Show dates, coverage, counts, and historical-only labels; suppress unsupported answers. I own corrections and disabling AI. Raw records identify referees; modeled tables contain teams/matches, not player profiles. Exclude referee names and visitor personal information from LLM inputs; redact sensitive logs. Resolve publication rights before exposing provider data ([data dictionary](data_dictionary.md)).

The AI must **never place bets, transfer money, promise profit, invent injuries/odds, expose secrets, run arbitrary SQL, or alter source records**. Allow only parameterized read tools and restricted draft/audit writes; require my approval before publishing agent drafts. Treat retrieved text as data, not instructions. Password-protect paid AI access and rate-limit requests. Database grants remain a template and must be verified before deployment.

## 6. Scorecard self-assessment — version 1

| Implementation Scorecard factor | Rating and justification |
|---|---|
| 1. Real user and workflow | Green — My match-selection workflow has eight timed baseline entries. |
| 2. Data access | Red — Current-season access, five-league coverage, and publication rights remain unverified. |
| 3. Data understanding | Green — The dictionary and question log document nulls, season meanings, unequal windows, and missing evidence. |
| 4. Freshness and monitoring | Red — Scheduled refreshes, correction detection, and failure alerts are not demonstrated. |
| 5. Grounding | Yellow — Verified SQL answers exist, but chatbot citations and refusals remain untested. |
| 6. Bounded autonomy | Yellow — Read tools and approval limits are specified, but enforced grants remain unverified. |
| 7. Evaluation | Yellow — Example answers exist, but repeatable golden-question and refusal tests are pending. |
| 8. Measured value and cost | Yellow — Baseline times and cost estimates exist, but net benefits including labor are unmeasured. |
| 9. Adoption | Yellow — I have a documented need, but website use and trust are not yet observed. |
| 10. Governance and accountability | Yellow — I own corrections, but public-release protections still require implementation and testing. |

**Two weakest:** **Data access:** in M3, I will test required league/season endpoints and clarify display rights before publication; unavailable coverage stays excluded. **Freshness and monitoring:** in M3–4, I will record sync outcomes and last-success times, test corrections and failed runs, and flag data older than 24 hours for current-match use; stale data must block current recommendations and prompt my review.
