"""Deterministic, explainable escalation routing.

Kept separate from the LLM layer (``agent.py``) and free of any dependency on
``models.py`` so the exact same rule can both route a new escalation and
reconstruct the "why was this routed here?" explanation for an existing one
purely from its stored severity + reason text — nothing about the routing
decision is hidden inside an opaque prompt.
"""
from __future__ import annotations


def route_escalation(severity: object, reason: str | None) -> tuple[str, str, str]:
    """Return (destination, priority, explanation) for a severity + reason pair."""
    text = (reason or "").lower()
    severity_key = str(getattr(severity, "value", severity) or "").lower()
    high_or_critical = severity_key in {"high", "critical"}

    if "academic" in text or high_or_critical:
        priority = "HIGH" if severity_key in {"high", "medium"} else "CRITICAL"
        matched = []
        if "academic" in text:
            matched.append('the reason mentions "academic"')
        if high_or_critical:
            matched.append(f"severity is {severity_key.upper()}")
        why = (
            " and ".join(matched)
            + " — academic issues and high-risk flags are routed to the Head of Department."
        )
        return "HOD", priority, why

    if "financial" in text:
        return (
            "Scholarship / Fee Section",
            "HIGH",
            'the reason mentions "financial" — financial difficulty is routed to the scholarship/fee section.',
        )

    if "personal" in text or "emotional" in text or "counselling" in text:
        matched_keyword = next(k for k in ("personal", "emotional", "counselling") if k in text)
        return (
            "Counselling Cell",
            "HIGH",
            f'the reason mentions "{matched_keyword}" — personal or emotional concerns are routed to the counselling cell.',
        )

    return (
        "Mentor",
        "MEDIUM",
        "no academic, financial or personal/emotional keyword was found and severity is not high or critical, "
        "so it stays with the mentor.",
    )
