"""
Laya decision-model classifier — a local, non-generative comparison point.

Laya is an encoder with decision heads: it reads the ticket plus a typed
"choice" question and returns a label with a confidence, in one forward pass.
No prompt/JSON parsing involved, so this is NOT a replacement for drafter.py —
it's an extra row for the eval table.

Usage (scores on TRAIN only, so holdout runs aren't spent):
    python -m src.laya_drafter
"""

from functools import lru_cache

import laya

# Option descriptions mirror the rules in policy.py (same train-ticket evidence).
QUESTIONS = {
    "action": {
        "type": "choice",
        "instructions": "What should customer support do with this ticket?",
        "criteria": {
            "escalate": (
                "legal or contract dispute, injury or safety issue, double charge or "
                "chargeback threat, fraud or scam accusation, broken promise or repeated "
                "unanswered contact"
            ),
            "clarify": (
                "customer reports a problem but does not say what is wrong, so support "
                "must ask a follow-up question; an order number alone is not enough detail"
            ),
            "reply": (
                "a specific question support can answer directly: order status, tracking, "
                "shipping, store hours, return policy, warranty, discounts; urgent wording "
                "alone does not change this"
            ),
        },
    }
}


@lru_cache(maxsize=1)
def _agent():
    return laya.load("convaiinnovations/laya")


def classify(ticket: dict) -> str:
    return classify_with_confidence(ticket)[0]


def classify_with_confidence(ticket: dict) -> tuple[str, float]:
    answer = _agent().predict(ticket["message"], QUESTIONS)["answers"]["action"]
    return answer["choice"], answer["confidence"]


def main():
    from src.eval import load_data, score, score_by_category

    train, _ = load_data()
    results = [classify_with_confidence(ticket) for ticket in train]
    predictions = [label for label, _ in results]
    gold = [ticket["gold_action"] for ticket in train]

    print(f"Laya on train: {score(predictions, gold)}")
    print(f"  by category: {score_by_category(predictions, train)}")
    print("\nMisses:")
    for ticket, (label, confidence) in zip(train, results):
        if label != ticket["gold_action"]:
            print(f"  {ticket['id']} gold={ticket['gold_action']} pred={label} ({confidence:.2f})  {ticket['message']}")


if __name__ == "__main__":
    main()
