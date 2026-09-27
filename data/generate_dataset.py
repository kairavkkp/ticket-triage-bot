"""
Generates a synthetic support-ticket dataset for the practice exercise.
Run once: `python data/generate_dataset.py`
Produces data/tickets.json (all tickets) and data/split.json (train/holdout ids ONLY).

Categories (the "gold_action" a human agent actually took):
  - reply     : answer directly with info already available (order status, policy, etc.)
  - escalate  : hand off to a human (angry customer, fraud/legal risk, ambiguous edge case)
  - clarify   : ask the customer a follow-up question before anything can be decided

Deliberately includes noisy signal: some "reply" tickets use words like "urgent" or
"terrible", and some "escalate" tickets are calm in tone — so a naive keyword baseline
will NOT trivially solve this. That's the point.
"""
import json
import random

random.seed(42)

REPLY_TEMPLATES = [
    "Hi, just checking on the status of order #{oid}. Any update?",
    "Where is my package for order #{oid}? Placed it 4 days ago.",
    "Can you confirm your return policy for items bought last week?",
    "What are your store hours this weekend?",
    "Do you ship to Canada? Wanted to check before ordering.",
    "I got a discount code, does it apply to sale items?",
    "This is urgent — I just need to know if order #{oid} has shipped yet.",
    "Quick question, does the warranty cover accidental drops?",
    "Is there a way to track order #{oid} in real time?",
    "Can I change the delivery address for order #{oid}? It hasn't shipped.",
]

ESCALATE_TEMPLATES = [
    "This is the third time my order #{oid} has been delayed. I want a refund NOW.",
    "I was charged twice for order #{oid}. This is unacceptable, fix it immediately.",
    "Your product injured my child. I need to speak to someone senior today.",
    "I think someone used my card without permission on order #{oid}.",
    "I've emailed 5 times about order #{oid} with no response. Absolutely furious.",
    "Legal here — we need to discuss a contract dispute regarding invoice #{oid}.",
    "The item arrived completely different from what was described, I feel scammed.",
    "I was told a manager would call me back about order #{oid} and nobody did.",
    "Can someone actually help me for once? Order #{oid} has been a nightmare.",
    "I'm considering a chargeback on order #{oid} unless this gets resolved today.",
]

CLARIFY_TEMPLATES = [
    "My order didn't arrive right.",
    "Something's wrong with what I got, can you help?",
    "I have an issue with a recent purchase.",
    "The product isn't working the way I expected.",
    "I need help with my account.",
    "Order #{oid} — there's a problem.",
    "Can you look into this for me?",
    "I'm not happy with my last order.",
    "There's an issue, please advise.",
    "Something seems off with order #{oid}.",
]

def make_ticket(i, category, template):
    oid = 10000 + i
    msg = template.format(oid=oid) if "{oid}" in template else template
    return {
        "id": f"t{i:03d}",
        "created_at": f"2026-0{random.randint(1,9)}-{random.randint(1,28):02d}T10:00:00Z",
        "channel": random.choice(["email", "chat", "sms"]),
        "message": msg,
        "gold_action": category,
    }

def main():
    tickets = []
    i = 0
    # Roughly matches real-world skew: most tickets are simple replies,
    # a meaningful minority need escalation or clarification.
    counts = {"reply": 30, "escalate": 15, "clarify": 15}
    pools = {"reply": REPLY_TEMPLATES, "escalate": ESCALATE_TEMPLATES, "clarify": CLARIFY_TEMPLATES}

    for category, n in counts.items():
        pool = pools[category]
        for _ in range(n):
            template = random.choice(pool)
            tickets.append(make_ticket(i, category, template))
            i += 1

    random.shuffle(tickets)

    # Lock a holdout split up front, by id only — mirrors the "lock before reading" rule.
    ids = [t["id"] for t in tickets]
    random.shuffle(ids)
    holdout_ids = sorted(ids[:15])          # 15 held out, never touched during "learning"
    train_ids = sorted(set(ids) - set(holdout_ids))

    with open("data/tickets.json", "w") as f:
        json.dump(tickets, f, indent=2)

    with open("data/split.json", "w") as f:
        json.dump({"train_ids": train_ids, "holdout_ids": holdout_ids}, f, indent=2)

    print(f"Wrote {len(tickets)} tickets -> data/tickets.json")
    print(f"Split locked -> data/split.json  (train={len(train_ids)}, holdout={len(holdout_ids)})")

if __name__ == "__main__":
    main()
