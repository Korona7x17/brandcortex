"""Playbook inspection and the approval gate (spec §10.3).

A system that rewrites its own instructions needs its instructions to be legible. These endpoints back
the playbook view: what is active, what the reflection agent proposed and on what evidence, and the
controls to approve or roll back.

Voice rules are visible here but never proposable — house voice is a fixed constraint (§10.4).
"""

from fastapi import APIRouter

router = APIRouter(prefix="/playbook", tags=["playbook"])


@router.get("")
def list_rules(brand: str, status: str | None = None) -> list[dict]:
    """TODO(phase-2)."""
    raise NotImplementedError


@router.post("/{rule_id}/approve")
def approve_rule(rule_id: str) -> dict:
    """Activate a proposed rule, retiring the previous version of the same key. TODO(phase-2)."""
    raise NotImplementedError


@router.post("/{rule_id}/rollback")
def rollback_rule(rule_id: str, to_version: int) -> dict:
    """Revert to an earlier version. Every change is revertible by design. TODO(phase-2)."""
    raise NotImplementedError


@router.get("/reports")
def list_reports(brand: str) -> list[dict]:
    """The reflection agent's human-readable 'what I learned' reports. TODO(phase-2)."""
    raise NotImplementedError
