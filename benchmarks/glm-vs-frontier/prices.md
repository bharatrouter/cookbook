# Price sheet

All cost figures in the benchmark are computed from this table — **official list prices,
fetched 2026-06-29**. INR conversions use **FX ₹96 / $1** (stated, not hidden). Re-verify the
sources before quoting; prices move.

## Frontier & budget (OpenAI / Anthropic — native APIs)

| Model | Model id | $/Mtok in | $/Mtok out | ₹/Mtok in | ₹/Mtok out | Source |
|---|---|---|---|---|---|---|
| Claude Opus 4.8 | `claude-opus-4-8` | 5.00 | 25.00 | 480 | 2400 | [Anthropic docs pricing](https://platform.claude.com/docs/en/about-claude/pricing) |
| Claude Sonnet 4.6 | `claude-sonnet-4-6` | 3.00 | 15.00 | 288 | 1440 | [Anthropic docs pricing](https://platform.claude.com/docs/en/about-claude/pricing) |
| Claude Haiku 4.5 | `claude-haiku-4-5` | 1.00 | 5.00 | 96 | 480 | [Anthropic docs pricing](https://platform.claude.com/docs/en/about-claude/pricing) |
| GPT-5.5 | `gpt-5.5` | 5.00 | 30.00 | 480 | 2880 | [OpenAI API pricing](https://developers.openai.com/api/docs/pricing) |
| GPT-5.4-mini | `gpt-5.4-mini` | 0.75 | 4.50 | 72 | 432 | [OpenAI API pricing](https://developers.openai.com/api/docs/pricing) |
| GPT-5.4-nano | `gpt-5.4-nano` | 0.20 | 1.25 | 19 | 120 | [OpenAI API pricing](https://developers.openai.com/api/docs/pricing) |

> Note: the original `gpt-5` id is delisted on OpenAI's current pricing page; GPT-5.5 is the
> current flagship. We benchmark the priced, callable ids above.

## GLM (via BharatRouter — catalog, INR-native)

Source: BharatRouter model catalog (`src/catalog.ts`). $ shown at FX ₹96/$.

| Model | Model id | Host | ₹/Mtok in | ₹/Mtok out | $/Mtok in | $/Mtok out |
|---|---|---|---|---|---|---|
| GLM-4.6 | `glm-4.6` | Zhipu | 58 | 211 | 0.60 | 2.20 |
| GLM-4.6 | `glm-4.6` | OpenRouter (BYOK) | 41 | 167 | 0.43 | 1.74 |
| GLM-4.7 | `glm-4.7` | Baseten (BYOK) | 58 | 211 | 0.60 | 2.20 |
| GLM-4.5-air | `glm-4.5-air` | Zhipu | 19 | 106 | 0.20 | 1.10 |
| GLM-4.7-flash | `glm-4.7-flash` | Zhipu / OpenRouter | 6 | 38 | 0.06 | 0.40 |

## Sangam (consensus) cost basis

Sangam runs multiple models per request, so its cost is the **sum of all member calls**
(panel × rounds + verifier + synthesizer). The harness records the *total* tokens BharatRouter
reports for the consensus call. In the blog tables, Sangam cost is computed from those real
total tokens priced at the **anchor model's rate** (GLM-4.7 ₹58/₹211 for `glm-sangam`) as a
clearly-labelled **upper bound** — the smaller open-weight panel members (Qwen, Llama) are
cheaper, so actual cost is lower. This is stated wherever a Sangam cost appears.
