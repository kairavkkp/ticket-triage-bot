"""
The eval harness. Run this ONCE against the holdout set per "version" of your
policy — don't rerun it every time you tweak the prompt, or you'll quietly
overfit to the holdout by trial and error (exactly what the lock is meant to
prevent).

TODO:
  1. Load data/tickets.json and data/split.json.
  2. Build train_tickets and holdout_tickets from the ids.
  3. Run all baselines (always_reply, keyword_baseline, majority_class_baseline)
     on the holdout set and print their accuracy.
  4. Run the real drafter (src/drafter.draft) on the holdout set and print its
     accuracy.
  5. IMPORTANT: also print a per-category breakdown (reply / escalate / clarify)
     for each baseline AND the real model — not just the overall number.
     (This is the exact thing we pressure-tested earlier — don't skip it.)
  6. Print a short verdict: does the model clear every baseline in EVERY
     category, or does it just win on the easy majority class?

Usage:
    python -m src.eval
"""

import json
from src.baselines import always_reply, keyword_baseline, majority_class_baseline


def load_data():
    with open("data/tickets.json") as f:
        tickets = json.load(f)
    with open("data/split.json") as f:
        split = json.load(f)
    by_id = {t["id"]: t for t in tickets}
    train = [by_id[i] for i in split["train_ids"]]
    holdout = [by_id[i] for i in split["holdout_ids"]]
    return train, holdout


def score(predictions: list[str], gold: list[str]) -> float:
    """exact-match accuracy. predictions[i] must equal gold[i]."""
    assert len(predictions) == len(gold), "predictions and gold must have the same length"
    return sum(1 for p, g in zip(predictions, gold) if p == g) / len(predictions)


def score_by_category(predictions: list[str], tickets: list[dict]) -> dict:
    """return {category: accuracy} for each gold_action category present."""
    categories = set(ticket["gold_action"] for ticket in tickets)
    return {
        category: score(
            [p for p, ticket in zip(predictions, tickets) if ticket["gold_action"] == category],
            [ticket["gold_action"] for ticket in tickets if ticket["gold_action"] == category],
        )
        for category in categories
    }


def main():
    train, holdout = load_data()
    # wire everything together per the docstring above.
    gold = [ticket["gold_action"] for ticket in holdout]
    majority_label = majority_class_baseline(train)  # computed from train only
    baselines = {
        "Always reply": always_reply,
        "Keyword baseline": keyword_baseline,
        "Majority class baseline": lambda ticket: majority_label,
    }

    print("Baselines:")
    baseline_by_category = {}
    for name, baseline in baselines.items():
        predictions = [baseline(ticket) for ticket in holdout]
        baseline_by_category[name] = score_by_category(predictions, holdout)
        print(f"{name}: {score(predictions, gold)}")
        print(f"  by category: {baseline_by_category[name]}")

    # Imported here so the baselines still run if a model backend isn't installed.
    from src import laya_drafter, ollama_drafter

    models = {
        f"Ollama {ollama_drafter.MODEL} (think={ollama_drafter.THINK})": lambda t: ollama_drafter.draft(t)["action"],
        "Laya (comparison only)": laya_drafter.classify,
    }

    print("\nModels:")
    model_by_category = {}
    for name, model in models.items():
        predictions = [model(ticket) for ticket in holdout]
        model_by_category[name] = score_by_category(predictions, holdout)
        print(f"{name}: {score(predictions, gold)}")
        print(f"  by category: {model_by_category[name]}")
        for ticket, prediction in zip(holdout, predictions):
            if prediction != ticket["gold_action"]:
                print(f"  miss {ticket['id']}: gold={ticket['gold_action']} pred={prediction}")

    # Verdict for the primary model: compare against the best baseline per category.
    # The keyword baseline can hit 100%, so "beats" may be impossible — report ties.
    primary = next(iter(models))
    print(f"\nVerdict for {primary}:")
    for category in sorted(model_by_category[primary]):
        model_acc = model_by_category[primary][category]
        best_name, best_acc = max(
            ((name, accs[category]) for name, accs in baseline_by_category.items()), key=lambda x: x[1]
        )
        outcome = "BEATS" if model_acc > best_acc else "TIES" if model_acc == best_acc else "LOSES TO"
        print(f"  {category}: {model_acc:.2f} {outcome} best baseline ({best_name}, {best_acc:.2f})")


if __name__ == "__main__":
    main()
