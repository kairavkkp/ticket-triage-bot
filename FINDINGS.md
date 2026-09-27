# Findings: Ticket Triage Bot

Results from Round 1: baselines, policy prompt, drafter and eval. The drafter
runs locally on Ollama (`qwen3.5:9b`) instead of the paid Claude API.

## Summary

- **`qwen3.5:9b` scores 15/15 on holdout**, getting every reply, escalate and
  clarify ticket right.
- **The keyword baseline also scores 15/15.** The model ties it in every
  category but can't beat it, because the dataset is built from a small set of
  templates.
- **Always-reply and majority-class score 60% while never escalating.** The
  per-category breakdown is what exposes this.
- **Laya**, a local encoder classifier, scored 67% and missed 4 of 5 holdout
  escalations. It isn't usable here.
- **Qwen's thinking mode isn't worth it** for this task: it gave the same
  accuracy at about 13 times the latency.

## Setup

| Piece | File | Notes |
|---|---|---|
| Baselines | `src/baselines.py` | always-reply, keyword rules, majority class (from train) |
| Policy prompt | `src/policy.py` | Ordered rules (escalate → clarify → reply), each backed by train tickets |
| LLM drafter | `src/ollama_drafter.py` | Ollama, JSON-schema-constrained output, fallback to `escalate` on bad output |
| Laya comparison | `src/laya_drafter.py` | Encoder "choice" question, no prompt or JSON |
| Eval | `src/eval.py` | Overall and per-category accuracy, plus a verdict against the best baseline per category |

Hardware: M1 Pro with 16 GB of RAM. Commands:

```bash
ollama pull qwen3.5:9b
python -m src.ollama_drafter   # train only
python -m src.eval             # holdout: run sparingly
```

## Data

There are 60 tickets: 45 in train and 15 in holdout. The split is fixed by id.

| Split | reply | clarify | escalate |
|---|---|---|---|
| Train | 21 (47%) | 14 (31%) | 10 (22%) |
| Holdout | 9 (60%) | **1 (7%)** | 5 (33%) |

## Results

### Holdout (15 tickets, one run)

| System | Overall | reply (9) | escalate (5) | clarify (1) |
|---|---|---|---|---|
| Always reply | 60% | 100% | 0% | 0% |
| Majority class (`reply`) | 60% | 100% | 0% | 0% |
| Keyword baseline | **100%** | 100% | 100% | 100% |
| **qwen3.5:9b, thinking off** | **100%** | 100% | 100% | 100% |
| Laya (comparison only) | 67% | 100% | 20% | 0% |

The eval's verdict is that the model **TIES** the best baseline in all three
categories.

### Train (45 tickets, used while developing)

| System | Overall | Misses | Speed |
|---|---|---|---|
| Keyword baseline | 97.8% | t056 | n/a |
| llama3.1 (8B) | 97.8% | t043 | 0.9 s/ticket |
| qwen3.5:9b, thinking off | 97.8% → **100%** after the prompt fix | t043 → none | 3.4–3.9 s/ticket |
| qwen3.5:9b, thinking on | 97.8% | t043 | 50 s/ticket |
| Laya, short option descriptions | 84% | 4 escalate, 3 clarify | n/a |
| Laya, full `SYSTEM_PROMPT` as instructions | 76% | 7 reply sent to clarify | n/a |

## Findings

**1. The keyword baseline is effectively the ceiling on this data.**
The tickets come from templates, and holdout reuses the same phrasings as
train. Some holdout messages are word-for-word copies of train messages. Ten
keywords chosen from train get 15/15 on holdout. On this data, a 20-line rule
matches the LLM with no model and no latency. The real case for the LLM is
wording the templates don't cover. This dataset can't measure that, so the
"beats every baseline" bar in the eval can at best be a tie.

**2. Overall accuracy hides the failures that matter.**
Always-reply and majority-class both score 60% and escalate nothing: every legal
threat, injury report and chargeback threat would get an automated reply. Those
failures only show up in the per-category breakdown. If a system scores 85%
overall but only 40% on escalate, it shouldn't ship. Escalate is the costly
category to get wrong, and it's the one where accuracy is lowest.

**3. The model's one train miss was a gap in the prompt, not in the model.**
llama3.1 and Qwen (with thinking on and off) all missed the same ticket, t043:
*"Can someone actually help me for once? Order #10043 has been a nightmare."*
All three gave the same reason: the customer doesn't say what the problem is.
That was a correct reading of the rules as written. The broken-promise rule
required concrete evidence, such as an unanswered callback or repeated contact.
Broadening it to cover customers who say support has repeatedly failed them
("help me for once", "been a nightmare") fixed t043 without breaking any other
train ticket. When different models make the same mistake, check the policy
before switching models.

**4. The two traps the prompt spells out were needed.**
- **Urgent wording doesn't mean escalate.** t003 and t013 are marked "urgent"
  but are labelled `reply`.
- **An order number doesn't make a complaint specific.** t045, t052, t054 and
  t057 all include one and are still `clarify`. The original hint in
  `policy.py` ("no order id → clarify") would have pointed the wrong way.

**5. Laya can't follow a written policy.**
Laya is an encoder: it scores each option against the text rather than reading
and following instructions. It can't apply ordered rules, exceptions or
tie-breaks. Replacing its short option descriptions with the full system prompt
made it worse (84% → 76% on train), because the long text pulled simple reply
tickets toward clarify. Its confidence scores aren't usable either: the
checkpoint prints a warning that they're uncalibrated, and correct and wrong
predictions have overlapping confidences (0.00–0.30).

**6. Thinking mode wasn't worth it.**
With thinking on, Qwen was just as accurate at 50 s/ticket compared with
3.9 s/ticket. Three-way classification with explicit rules doesn't benefit from
it.

**7. Constrained decoding made parsing reliable.**
Ollama's `format` option (a JSON schema with an `enum` on `action`) prevents
invalid labels and text outside the JSON. Across every run there were no parse
failures and no fallbacks. The fallback to `escalate` stays in the code as a
backstop: a wrong escalation costs an agent a minute, while a wrong reply can
leave a legal ticket unhandled.

## Caveats

- **The holdout is small and lopsided.** Its 15 tickets include only **one**
  clarify ticket, so "100% clarify" means 1/1. The split was a random shuffle
  that didn't keep label proportions.
- **Holdout overlaps train.** Several holdout messages appear word-for-word in
  train, so holdout scores overstate how well any system generalizes.
- **Ticket ids give away the label.** ids t000–t029 are all reply, t030–t044
  escalate and t045–t059 clarify. No system here uses the id, but a future
  change must not pass it to a model.
- **Holdout was used once for the model.** The prompt fix for t043 was made
  from train results, before the single holdout run. While profiling the data
  at the start, a few holdout rows were printed. They weren't used to write
  the prompt or the keywords.

## Next steps

1. **Write 10–20 tickets by hand** in wording the templates don't use
   ("I'm contacting my attorney", "my card got hit two times"), and keep them
   as a separate test set. That's the only way to show the LLM doing better
   than the keyword baseline.
2. **Re-split with the label proportions preserved** and with duplicate
   messages removed across splits, so holdout means something. This changes
   the locked holdout, so it's a deliberate reset.
3. **Round 2:** `store.py` (deduplication and optimistic concurrency) and
   `review_cli.py` (human approval loop).
