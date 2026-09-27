"""
Dumb baselines. These must NOT call the LLM — they exist purely to give the real
model something to beat. Implement all three; each takes a ticket dict and
returns one of "reply" | "escalate" | "clarify".
"""

from collections import Counter


def always_reply(ticket: dict) -> str:
    return "reply"


ESCALATE_KEYWORDS = [
    "legal",
    "contract",
    "chargeback",
    "charged twice",
    "injured",
    "scammed",
    "furious",
    "manager",
    "no response",
    "nightmare",
]

CLARIFY_KEYWORDS = [
    "problem",
    "issue",
    "wrong",
    "not happy",
    "isn't working",
    "seems off",
    "need help",
]


def keyword_baseline(ticket: dict) -> str:
    message = ticket["message"].lower()
    if any(kw in message for kw in ESCALATE_KEYWORDS):
        return "escalate"
    if any(kw in message for kw in CLARIFY_KEYWORDS):
        return "clarify"
    return "reply"


def majority_class_baseline(train_tickets: list[dict]) -> str:
    all_gold_actions = map(lambda obj: obj["gold_action"], train_tickets)
    return Counter(all_gold_actions).most_common(1)[0][0]
