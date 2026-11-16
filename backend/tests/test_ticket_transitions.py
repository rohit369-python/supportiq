"""Ticket status transition rules."""

from app.api.v1.tickets import VALID_TRANSITIONS


def test_new_can_become_open():
    assert "open" in VALID_TRANSITIONS["new"]


def test_resolved_can_reopen():
    assert "reopened" in VALID_TRANSITIONS["resolved"]


def test_closed_cannot_go_to_in_progress():
    assert "in_progress" not in VALID_TRANSITIONS["closed"]


def test_critical_paths_exist():
    for status in ["new", "open", "in_progress", "resolved", "closed", "reopened"]:
        assert status in VALID_TRANSITIONS