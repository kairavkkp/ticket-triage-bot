"""
The "drafter": reads one ticket, calls Claude, returns a structured decision.
Mirrors the field-guide idea that this half has NO tools — it only classifies
text and returns JSON. It never sends anything itself.

Install first:  pip install anthropic
Set your key:   export ANTHROPIC_API_KEY=sk-ant-...
"""

import json
import os
from anthropic import Anthropic
from src.policy import SYSTEM_PROMPT, OUTPUT_SCHEMA_HINT

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

MODEL = "claude-sonnet-4-6"


def draft(ticket: dict) -> dict:
    """
    Calls Claude with the ticket message, returns a dict like:
      {"action": "reply", "reason": "..."}

    TODO:
      1. Build the user message from ticket["message"].
      2. Call client.messages.create(...) with SYSTEM_PROMPT + OUTPUT_SCHEMA_HINT.
      3. Parse the response text as JSON.
      4. Handle the failure case: what do you do if the model doesn't return
         valid JSON, or returns an action that isn't one of the 3 allowed values?
         (Don't just crash — decide on a safe fallback, and log that it happened.)
    """
    raise NotImplementedError
