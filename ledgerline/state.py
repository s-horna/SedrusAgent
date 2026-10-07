"""Persistent household state: a relational model stored as one JSON file.

Each top-level map is a table keyed by a stable ID; records reference each
other by ID. `claims` is append-only (what documents said); `entities` and
`roles` are what we currently believe; `questions` is the human queue.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

SCHEMA_VERSION = 1

EntityKind = Literal["person", "trust", "company", "account"]
DocumentStatus = Literal["processed", "needs_review"]
RoleStatus = Literal["active", "superseded", "disputed"]
# "unverified_quote" is no longer raised; it stays so older state files still load.
QuestionKind = Literal["possible_duplicate", "conflict", "unverified_quote", "unreadable"]
QuestionStatus = Literal["open", "resolved"]


class Document(BaseModel):
    id: str
    filename: str
    sha256: str
    doc_type: str | None = None
    doc_date: date | None = None
    ingested_at: datetime
    extraction_model: str | None = None
    status: DocumentStatus = "processed"


class Entity(BaseModel):
    id: str
    kind: EntityKind
    name: str
    aliases: list[str] = Field(default_factory=list)
    # Strong identifiers used for auto-linking (e.g. ssn_last4, dob, ein, account_last4, custodian).
    identifiers: dict[str, str] = Field(default_factory=dict)
    sources: list[str] = Field(default_factory=list)  # claim IDs


class Role(BaseModel):
    id: str
    subject: str  # entity ID
    role: str
    object: str  # entity ID
    qualifiers: dict[str, str] = Field(default_factory=dict)
    effective_from: date | None = None
    effective_to: date | None = None
    status: RoleStatus = "active"
    sources: list[str] = Field(default_factory=list)  # claim IDs


class Claim(BaseModel):
    id: str
    document: str
    page: int | None = None
    quote: str
    assertion: dict[str, Any]
    resolved_to: str | None = None  # entity or role ID once applied


class Question(BaseModel):
    id: str
    kind: QuestionKind
    summary: str
    candidates: list[str] = Field(default_factory=list)
    blocking_claims: list[str] = Field(default_factory=list)
    raised_by: str  # document ID
    status: QuestionStatus = "open"
    resolution: str | None = None


class State(BaseModel):
    schema_version: int = SCHEMA_VERSION
    documents: dict[str, Document] = Field(default_factory=dict)
    entities: dict[str, Entity] = Field(default_factory=dict)
    roles: dict[str, Role] = Field(default_factory=dict)
    claims: dict[str, Claim] = Field(default_factory=dict)
    questions: dict[str, Question] = Field(default_factory=dict)


def stable_id(prefix: str, *parts: object) -> str:
    """Deterministic ID so re-running the same input yields the same records."""
    payload = json.dumps(parts, sort_keys=True, default=str)
    return f"{prefix}_{hashlib.sha256(payload.encode()).hexdigest()[:12]}"


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path: Path) -> State:
    if not path.exists():
        return State()
    return State.model_validate_json(path.read_text(encoding="utf-8"))


def save(state: State, path: Path) -> None:
    """Atomic write: temp file in the same directory, then rename over the target."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = state.model_dump_json(indent=2)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(data)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
