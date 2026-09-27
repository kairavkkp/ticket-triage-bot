"""
Stretch goal. A minimal command-line "approval screen" — the human-in-the-loop
gate. Run this against a few train tickets (never the holdout — that's for
eval.py only).

TODO:
  1. For each ticket: call src.drafter.draft(ticket) to get a proposed action.
  2. Show the ticket + the model's proposed action + reason to the user.
  3. Ask for one of: [a]pprove / [e]dit / [d]iscard.
     - approve: save as-is via store.save_review(...), status="approved".
     - edit: prompt for a corrected action, save BOTH the original draft AND
       the human's correction (this pair is your feedback-loop training data
       — don't overwrite the original).
     - discard: log it as discarded, no further action.
  4. Append every draft/correction pair to data/feedback_log.jsonl so you can
     later analyze "what does the model consistently get wrong."
  5. Nothing in this file should ever be able to actually "send" anything —
     there is no send function here on purpose. That's the point of the
     drafter/fetcher split: this script only writes to your own local store.

Usage:
    python -m src.review_cli
"""


def main():
    raise NotImplementedError


if __name__ == "__main__":
    main()
