"""
Local drafter: same contract as drafter.draft(), but runs on Ollama instead of
the paid Claude API. Reads one ticket, returns {"action": ..., "reason": ...}.
It never sends anything itself.

Setup:
    ollama pull qwen3.5:9b
    pip install ollama

Usage (scores on TRAIN only, so holdout runs aren't spent):
    python -m src.ollama_drafter
    OLLAMA_MODEL=qwen3.5:4b OLLAMA_THINK=1 python -m src.ollama_drafter
"""

import json
import logging
import os

import ollama

from src.policy import OUTPUT_SCHEMA_HINT, SYSTEM_PROMPT

MODEL = os.environ.get("OLLAMA_MODEL", "qwen3.5:9b")
THINK = os.environ.get("OLLAMA_THINK", "0") == "1"

ACTIONS = ["reply", "escalate", "clarify"]

# Ollama constrains decoding to this schema, so "action" can only be one of ACTIONS.
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": ACTIONS},
        "reason": {"type": "string"},
    },
    "required": ["action", "reason"],
}

# If the output is unusable, route to a human: a wrong escalate costs an agent a
# minute, a wrong reply/clarify can leave a legal or injury ticket unhandled.
FALLBACK_ACTION = "escalate"

log = logging.getLogger(__name__)


def draft(ticket: dict) -> dict:
    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT + OUTPUT_SCHEMA_HINT},
            {"role": "user", "content": ticket["message"]},
        ],
        format=OUTPUT_SCHEMA,
        think=THINK,
        options={"temperature": 0},
    )
    return parse(response.message.content, ticket["id"])


def parse(text: str, ticket_id: str) -> dict:
    try:
        result = json.loads(text)
        action = result["action"]
    except (json.JSONDecodeError, KeyError, TypeError):
        log.warning("ticket %s: unparseable output %r, falling back to %s", ticket_id, text, FALLBACK_ACTION)
        return {"action": FALLBACK_ACTION, "reason": "fallback: unparseable model output"}
    if action not in ACTIONS:
        log.warning("ticket %s: invalid action %r, falling back to %s", ticket_id, action, FALLBACK_ACTION)
        return {"action": FALLBACK_ACTION, "reason": f"fallback: invalid action {action!r}"}
    return {"action": action, "reason": result.get("reason", "")}


def main():
    import time

    from src.eval import load_data, score, score_by_category

    logging.basicConfig(level=logging.WARNING)
    train, _ = load_data()

    start = time.time()
    drafts = [draft(ticket) for ticket in train]
    elapsed = time.time() - start

    predictions = [d["action"] for d in drafts]
    gold = [ticket["gold_action"] for ticket in train]

    print(f"{MODEL} (think={THINK}) on train: {score(predictions, gold)}  [{elapsed / len(train):.1f}s/ticket]")
    print(f"  by category: {score_by_category(predictions, train)}")
    print("\nMisses:")
    for ticket, d in zip(train, drafts):
        if d["action"] != ticket["gold_action"]:
            print(f"  {ticket['id']} gold={ticket['gold_action']} pred={d['action']}  {ticket['message']}")
            print(f"      reason: {d['reason']}")


if __name__ == "__main__":
    main()
