# Practice exercise: Ticket Triage Bot

A scaled-down version of everything we've been discussing, sized to build in
one sitting — good practice for a live-coding-style technical round about AI
pipelines.

## Setup

```bash
cd ticket-triage-bot
pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-...   # your own key
python data/generate_dataset.py       # already run once, re-run any time to reset
```

## The problem

You're building a bot that reads a support ticket and decides one of three
actions: **reply** (answer directly), **escalate** (hand to a human), or
**clarify** (ask a follow-up question first). You have 60 historical tickets
with the real action a human agent took (`data/tickets.json`), already split
into a locked train/holdout set (`data/split.json` — don't peek at holdout
ticket *content*, only use it for scoring).

## Do it in this order (this order is part of the exercise)

**Round 1 practice — core loop, aim for ~45–60 min:**
1. `src/baselines.py` — implement `keyword_baseline` and
   `majority_class_baseline`. No LLM calls allowed in this file.
2. `src/policy.py` — write the actual policy/prompt. Look at `data/tickets.json`
   train tickets only for inspiration (or the ids in `split.json["train_ids"]`
   if you want to be strict about it).
3. `src/drafter.py` — wire up the Claude API call and safe JSON parsing.
4. `src/eval.py` — implement scoring, run it **once**, and get:
   - overall accuracy for every baseline + your model
   - a **per-category** breakdown for each (this is the part people skip —
     don't skip it)
5. Look at the breakdown. If your model doesn't clearly beat every baseline in
   every category, go fix `policy.py`, but **do not re-run eval.py against
   holdout more than once or twice** — pretend each run costs something, like
   it would for real.

**Round 2 practice — the harder half, aim for another ~45–60 min:**
6. `src/store.py` — idempotent dedup + optimistic concurrency, backed by sqlite.
7. `src/review_cli.py` — a human approval loop that never sends anything, and
   logs every draft/correction pair for future learning.

## Self-check when you're done (say these out loud, like you would on a call)

- [ ] Can you explain, without looking at code, *why* `majority_class_baseline`
      might score deceptively high on this dataset?
- [ ] Can you point to one training ticket that justifies a specific rule in
      your policy prompt?
- [ ] If your overall accuracy is 85% but escalate-category accuracy is 40%,
      what would you say to a PM who wants to ship it?
- [ ] In `store.py`, what actually happens if two review calls hit
      `claim_and_draft` for the same ticket id at the same instant?
- [ ] In `review_cli.py`, why is there deliberately no `send()` function
      anywhere in this file?

## Timing yourself

Since the real round is about *speed with correctness*, try running through
Round 1 twice: once untimed to get it right, once timed to see how close you
can get to 30–40 minutes for steps 1–5. That gap between "correct" and "correct
and fast" is what the actual interview is testing.
# ticket-triage-bot
