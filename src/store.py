"""
Stretch goal (do this after eval.py + drafter.py work end to end).

A tiny sqlite-backed store that gives you two real guarantees:
  1. Idempotent drafting: the same ticket id can never be drafted twice.
  2. Optimistic concurrency: a review can only be saved if it's still editing
     the version it started from (no silent overwrite of someone else's edit).

TODO:
  1. Create a sqlite table `drafts` with columns:
     ticket_id (unique), draft_json, version (int, starts at 1), status
     (drafted | approved | sent), human_edit_json (nullable).
  2. claim_and_draft(ticket, draft_fn): insert a row for ticket["id"] ONLY if
     it doesn't already exist (use a uniqueness constraint, not a manual
     SELECT-then-INSERT check — that has a race condition). If the insert is
     rejected because the row exists, just return the existing draft instead
     of calling draft_fn again.
  3. save_review(ticket_id, expected_version, human_edit, new_status):
     UPDATE ... WHERE ticket_id = ? AND version = ?. Check rows affected.
     If 0 rows were updated, someone else changed it first — raise/report a
     conflict instead of silently succeeding. On success, increment version.
"""

import sqlite3

DB_PATH = "data/store.db"


def init_db():
    """TODO: create the drafts table if it doesn't exist."""
    raise NotImplementedError


def claim_and_draft(ticket: dict, draft_fn):
    """TODO: see docstring above."""
    raise NotImplementedError


def save_review(
    ticket_id: str, expected_version: int, human_edit: dict, new_status: str
):
    """TODO: see docstring above. Return True on success, False on version conflict."""
    raise NotImplementedError
