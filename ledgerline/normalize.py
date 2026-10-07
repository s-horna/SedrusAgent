"""Canonical forms for identifiers and dates so exact matching works across documents."""

from __future__ import annotations

import re
from datetime import date, datetime

_DATE_FORMATS = ["%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%B %d, %Y", "%b %d, %Y", "%d %B %Y", "%B %d %Y"]


def normalize_date(value: str) -> str:
    """Return YYYY-MM-DD when the value parses, else the stripped input."""
    v = value.strip().replace("Sept ", "Sep ")
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(v, fmt).date().isoformat()
        except ValueError:
            continue
    return v


def parse_date(value: object) -> date | None | object:
    """Pydantic before-validator helper: accept common written date formats."""
    if isinstance(value, str):
        if not value.strip():
            return None
        return normalize_date(value)
    return value


def normalize_identifier(key: str, value: str) -> str:
    value = str(value).strip()
    if key.endswith("last4"):
        digits = re.sub(r"\D", "", value)
        return digits[-4:] if len(digits) >= 4 else value
    if key in ("dob", "trust_date"):
        return normalize_date(value)
    if key == "custodian":
        return re.sub(r"\s+", " ", value)
    return value


def normalize_identifiers(identifiers: dict[str, str]) -> dict[str, str]:
    return {k: normalize_identifier(k, v) for k, v in identifiers.items() if str(v).strip()}


def identifiers_equal(key: str, a: str, b: str) -> bool:
    if key == "custodian":
        # "Schwab" vs "Charles Schwab & Co., Inc."
        na, nb = _alnum(a), _alnum(b)
        return bool(na and nb) and (na in nb or nb in na)
    return a == b


def _alnum(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


_SSN = re.compile(r"\b\d{3}[- ]{1,3}\d{2}[- ]{1,3}\d{4,5}\b")


def redact_ssns(text: str) -> str:
    """Mask SSN-shaped numbers to their last 4 digits before anything is stored."""
    return _SSN.sub(lambda m: "XXX-XX-" + re.sub(r"\D", "", m.group())[-4:], text)


def malformed_ssn_last4s(text: str) -> set[str]:
    """Last 4 digits of SSN-shaped numbers that don't have exactly 9 digits."""
    found = set()
    for m in _SSN.finditer(text):
        digits = re.sub(r"\D", "", m.group())
        if len(digits) != 9:
            found.add(digits[-4:])
    return found
