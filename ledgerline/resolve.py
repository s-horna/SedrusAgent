"""Step 4: deterministic code decides how an extraction changes the records.

Policy (deliberately conservative):
- A mention links to an existing entity on an exact strong-identifier match, or
  on an exact full name (first, middle, last) when no other similar name exists.
  A name that merely resembles an existing entity becomes a question; it is
  never merged and never created. A mention with no similar entity is created.
  People resemble only with the same surname, compatible first names (equal, or
  an initial) and no conflicting middle initial. Entities created from the same
  document are never treated as lookalikes of each other.
- A role claim is applied only once both sides are resolved.
- Re-asserting a known role adds a source (corroboration).
- A control role (trustee, owner, signer, ...) asserted by a document for a
  different holder than other documents established becomes a conflict
  question, and both sides are marked disputed.
- A role ends (superseded) only when a document with authority over that role
  says so explicitly; otherwise the end claim becomes a conflict question.
- A trust with exactly the same name as a known trust but a different trust
  date is the same trust with a date conflict: it links, and the dates become a
  conflict question. A trust agreement or amendment's date wins.
- SSN-shaped numbers are masked to their last 4 digits before anything is
  stored, and a malformed SSN (not 9 digits) never yields an ssn_last4.
"""

from __future__ import annotations

import re
from datetime import date

from ledgerline.extract import ExtractedClaim, ExtractionResult, Mention
from ledgerline.normalize import identifiers_equal, malformed_ssn_last4s, redact_ssns
from ledgerline.state import Claim, Entity, Question, Role, State, stable_id

ID_PREFIX = {"person": "per", "trust": "tru", "company": "co", "account": "acc"}

# Identifier sets that, when all present and equal, identify the same entity.
STRONG_KEYS: dict[str, list[tuple[str, ...]]] = {
    "person": [("ssn_last4", "dob"), ("ssn_last4",), ("dob",)],
    "trust": [("trust_date",)],
    "company": [("ein_last4",)],
    "account": [("custodian", "account_last4")],
}

# Roles that let someone act on or move money: a disagreement is never auto-resolved.
CONTROL_ROLES = {
    "grantor", "trustee", "successor_trustee", "owner",
    "authorized_signer", "power_of_attorney", "manager",
}

# Which document types may END a role. Anything else saying a role ended goes to a human.
AUTHORITY: dict[str, set[str]] = {
    "trust_agreement": {"trustee", "successor_trustee", "beneficiary"},
    "trust_amendment": {"trustee", "successor_trustee", "beneficiary"},
    "account_application": {"owner", "authorized_signer"},
    "operating_agreement": {"member", "manager"},
    "power_of_attorney": {"power_of_attorney"},
}


def _norm(name: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", name.lower())).strip()


# "il"/"ill" are how some printers and OCR render "II"/"III".
_SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "il", "ill"}


def _given_names_compatible(a: str, b: str) -> bool:
    """Same name, or one is an initial of the other: "M" vs "Margaret"."""
    return a == b or (min(len(a), len(b)) == 1 and a[0] == b[0])


def _uninvert(name: str) -> str:
    """"SMITH III, JOHN D." -> "JOHN D. SMITH III". Leaves "John Smith, Jr." alone."""
    if name.count(",") != 1:
        return name
    surname, given = (p.strip() for p in name.split(","))
    if not surname or not given or all(t in _SUFFIXES for t in _norm(given).split()):
        return name
    return f"{given} {surname}"


def _names_resemble(kind: str, a: str, b: str) -> bool:
    if kind == "person":
        a, b = _uninvert(a), _uninvert(b)
    na, nb = _norm(a), _norm(b)
    if na == nb or (len(na) > 8 and (na in nb or nb in na)):
        return True
    ta, tb = na.split(), nb.split()
    if kind != "person":
        return bool(ta and tb and ta[-1] == tb[-1] and ta[0][0] == tb[0][0])
    # Same surname, compatible first names, and middle initials that don't conflict.
    # Two different full first names ("Jordan" vs "Jane") are two people.
    ta = [t for t in ta if t not in _SUFFIXES]
    tb = [t for t in tb if t not in _SUFFIXES]
    if len(ta) < 2 or len(tb) < 2 or ta[-1] != tb[-1]:
        return False
    if not _given_names_compatible(ta[0], tb[0]):
        return False
    ma, mb = ta[1:-1], tb[1:-1]
    return not (ma and mb and ma[0][0] != mb[0][0])


_OCR_SUFFIX = {"il": "ii", "ill": "iii"}


def _person_norm(name: str) -> str:
    """_norm in given-first order, with a final "Il"/"Ill" read as the suffix "II"/"III"."""
    tokens = _norm(_uninvert(name)).split()
    if len(tokens) > 2 and tokens[-1] in _OCR_SUFFIX:
        tokens[-1] = _OCR_SUFFIX[tokens[-1]]
    return " ".join(tokens)


def _full_name_equal(kind: str, name: str, entity: Entity) -> bool:
    """Exact name match (case/punctuation-insensitive). People need first, middle and last."""
    norm = _person_norm if kind == "person" else _norm
    n = norm(name)
    if len(n.split()) < (3 if kind == "person" else 2):
        return False
    return any(n == norm(x) for x in [entity.name, *entity.aliases])


def _same_trust_name(name: str, entity: Entity) -> bool:
    """Exact trust name, ignoring case, punctuation and a leading "The"."""
    def key(n: str) -> str:
        return re.sub(r"^the ", "", _norm(n))
    return any(key(name) == key(x) for x in [entity.name, *entity.aliases])


def _identifier_match(kind: str, idents: dict[str, str], entity: Entity) -> bool | None:
    """True = same entity, False = provably different, None = can't tell."""
    for keys in STRONG_KEYS[kind]:
        if all(k in idents and k in entity.identifiers for k in keys):
            return all(identifiers_equal(k, idents[k], entity.identifiers[k]) for k in keys)
    return None


def mention_claim_id(doc_id: str, ref: str) -> str:
    return stable_id("clm", doc_id, "mention", ref)


class Resolver:
    """Applies one document's claims to state."""

    def __init__(self, state: State, doc_id: str, doc_type: str | None):
        self.state = state
        self.doc_id = doc_id
        self.doc_type = doc_type or "other"
        # Entities created from this document. The model already told its own
        # mentions apart, so they are never lookalikes of each other.
        self.created: set[str] = set()

    # --- lookups -----------------------------------------------------------

    def _entity_for_ref(self, ref: str) -> str | None:
        claim = self.state.claims.get(mention_claim_id(self.doc_id, ref))
        return claim.resolved_to if claim else None

    def _open_question_holding(self, claim_id: str) -> Question | None:
        return next(
            (q for q in self.state.questions.values()
             if q.status == "open" and claim_id in q.blocking_claims),
            None,
        )

    def _role_claims_here(self) -> list[Claim]:
        return [c for c in self.state.claims.values()
                if c.document == self.doc_id and c.assertion["type"] == "role"]

    def _hold(self, question: Question, claim: Claim) -> None:
        if question.id not in self.state.questions:
            self.state.questions[question.id] = question
        q = self.state.questions[question.id]
        if claim.id not in q.blocking_claims:
            q.blocking_claims.append(claim.id)

    def _name(self, entity_id: str) -> str:
        e = self.state.entities.get(entity_id)
        return e.name if e else entity_id

    # --- intake ------------------------------------------------------------

    def add_mention(self, m: Mention) -> Claim:
        claim = Claim(
            id=mention_claim_id(self.doc_id, m.ref),
            document=self.doc_id,
            page=m.page,
            quote=redact_ssns(m.quote),
            assertion={"type": "mention", **m.model_dump(exclude={"page", "quote"})},
        )
        self.state.claims[claim.id] = claim
        return claim

    def add_role_claim(self, index: int, c: ExtractedClaim) -> Claim:
        claim = Claim(
            id=stable_id("clm", self.doc_id, "role", index),
            document=self.doc_id,
            page=c.page,
            quote=redact_ssns(c.quote),
            assertion={"type": "role", **c.model_dump(mode="json", exclude={"page", "quote"})},
        )
        self.state.claims[claim.id] = claim
        return claim

    # --- mentions ----------------------------------------------------------

    def place_mention(self, claim: Claim) -> None:
        """Link to an entity, create one, or raise a question."""
        a = claim.assertion
        kind, name, idents = a["kind"], a["name"], a["identifiers"]

        same_kind = [e for e in self.state.entities.values() if e.kind == kind]
        matches = [e for e in same_kind if _identifier_match(kind, idents, e) is True]
        if len(matches) == 1:
            self._link(claim, matches[0])
            return

        if kind == "trust" and not matches:
            same_name = [e for e in same_kind
                         if _identifier_match(kind, idents, e) is False and _same_trust_name(name, e)]
            if len(same_name) == 1:
                self._link_with_date_conflict(claim, same_name[0])
                return

        lookalikes = [e for e in same_kind
                      if e.id not in self.created and _identifier_match(kind, idents, e) is None
                      and _names_resemble(kind, name, e.name)]
        exact = [e for e in lookalikes if _full_name_equal(kind, name, e)]
        if not matches and len(exact) == 1 and len(lookalikes) == 1:
            self._link(claim, exact[0])
            return
        candidates = matches or lookalikes
        if candidates:
            self._hold(Question(
                id=stable_id("q", self.doc_id, a["ref"]),
                kind="possible_duplicate",
                summary=f"Is {kind} '{name}' the same as "
                        + " or ".join(f"{e.id} '{e.name}'" for e in candidates)
                        + "? Not merged or created until confirmed.",
                candidates=[e.id for e in candidates],
                raised_by=self.doc_id,
            ), claim)
            return

        self._create(claim)

    def _create(self, claim: Claim) -> None:
        a = claim.assertion
        entity = Entity(
            id=stable_id(ID_PREFIX[a["kind"]], self.doc_id, a["ref"]),
            kind=a["kind"],
            name=a["name"],
            identifiers=dict(a["identifiers"]),
        )
        self.state.entities[entity.id] = entity
        self.created.add(entity.id)
        self._link(claim, entity)

    def _link_with_date_conflict(self, claim: Claim, trust: Entity) -> None:
        new, old = claim.assertion["identifiers"]["trust_date"], trust.identifiers["trust_date"]
        kept = old
        if self.doc_type in ("trust_agreement", "trust_amendment"):
            trust.identifiers["trust_date"] = kept = new
        self._link(claim, trust)
        self.state.questions.setdefault(stable_id("q", self.doc_id, "trust_date", trust.id), Question(
            id=stable_id("q", self.doc_id, "trust_date", trust.id),
            kind="conflict",
            summary=f"Trust date for {trust.name}: this document says {new}, other documents say {old}. "
                    f"Treated as the same trust; the trust date is recorded as {kept} until confirmed.",
            candidates=[trust.id],
            raised_by=self.doc_id,
        ))

    def _link(self, claim: Claim, entity: Entity) -> None:
        name = claim.assertion["name"]
        if name != entity.name and name not in entity.aliases:
            entity.aliases.append(name)
        for k, v in claim.assertion["identifiers"].items():
            entity.identifiers.setdefault(k, v)
        if claim.id not in entity.sources:
            entity.sources.append(claim.id)
        claim.resolved_to = entity.id

    # --- roles -------------------------------------------------------------

    def apply_role(self, claim: Claim) -> None:
        a = claim.assertion
        subject, obj = self._entity_for_ref(a["subject_ref"]), self._entity_for_ref(a["object_ref"])
        if subject is None or obj is None:
            for ref in (a["subject_ref"], a["object_ref"]):
                q = self._open_question_holding(mention_claim_id(self.doc_id, ref))
                if q:
                    self._hold(q, claim)
            return

        role = a["role"]
        existing = self.state.roles.get(stable_id("rol", subject, role, obj))

        if a.get("ended"):
            self._end_role(claim, existing, subject, role, obj)
            return

        if existing:
            self._add_source(existing, claim)
            return

        new = Role(
            id=stable_id("rol", subject, role, obj),
            subject=subject, role=role, object=obj,
            qualifiers=dict(a.get("qualifiers") or {}),
            effective_from=a.get("effective_from"),
        )
        rivals = self._rivals(new) if role in CONTROL_ROLES else []
        self.state.roles[new.id] = new
        self._add_source(new, claim)
        if not rivals:
            return

        new.status = "disputed"
        for r in rivals:
            r.status = "disputed"
        holders = ", ".join(self._name(r.subject) for r in rivals)
        self._hold(Question(
            id=stable_id("q", self.doc_id, "conflict", claim.id),
            kind="conflict",
            summary=f"This document says {self._name(subject)} is {role} of {self._name(obj)}, "
                    f"but other documents say {holders}. All are marked disputed until confirmed.",
            candidates=[r.id for r in rivals],
            raised_by=self.doc_id,
        ), claim)

    def _rivals(self, new: Role) -> list[Role]:
        """Live holders of the same control role from other documents that this one doesn't name."""
        named_here = set()
        for c in self._role_claims_here():
            ca = c.assertion
            if ca["role"] == new.role and not ca.get("ended") \
                    and self._entity_for_ref(ca["object_ref"]) == new.object:
                named_here.add(self._entity_for_ref(ca["subject_ref"]))
        return [
            r for r in self.state.roles.values()
            if r.role == new.role and r.object == new.object and r.subject != new.subject
            and r.status in ("active", "disputed") and r.subject not in named_here
        ]

    def _end_role(self, claim: Claim, existing: Role | None, subject: str, role: str, obj: str) -> None:
        a = claim.assertion
        if role not in AUTHORITY.get(self.doc_type, set()):
            self._hold(Question(
                id=stable_id("q", self.doc_id, "conflict", claim.id),
                kind="conflict",
                summary=f"A {self.doc_type} says {self._name(subject)} is no longer {role} of "
                        f"{self._name(obj)}, but this document type can't change that role. "
                        "The role is left unchanged until confirmed.",
                candidates=[existing.id] if existing else [],
                raised_by=self.doc_id,
            ), claim)
            return
        if existing is None:  # end of a role we never saw start: keep it as history
            existing = Role(id=stable_id("rol", subject, role, obj), subject=subject, role=role, object=obj)
            self.state.roles[existing.id] = existing
        existing.status = "superseded"
        ended_on = a.get("effective_to") or a.get("effective_from")
        existing.effective_to = date.fromisoformat(ended_on) if ended_on else None
        self._add_source(existing, claim)

    @staticmethod
    def _add_source(role: Role, claim: Claim) -> None:
        if claim.id not in role.sources:
            role.sources.append(claim.id)
        claim.resolved_to = role.id


def apply_extraction(state: State, doc_id: str, result: ExtractionResult) -> list[str]:
    """Apply one document's extraction to state. Returns IDs of questions raised."""
    before = set(state.questions)
    r = Resolver(state, doc_id, result.doc_type)

    # A last4 taken from a malformed SSN (e.g. 10 digits) identifies no one.
    printed = "\n".join([*(m.quote for m in result.mentions),
                         *(c.quote for c in result.claims), *result.unreadable_notes])
    malformed = malformed_ssn_last4s(printed)
    for m in result.mentions:
        if m.identifiers.get("ssn_last4") in malformed:
            del m.identifiers["ssn_last4"]

    for m in result.mentions:
        r.place_mention(r.add_mention(m))

    # Endings first, so a replacement in the same document doesn't look like a conflict.
    ordered = sorted(enumerate(result.claims), key=lambda ic: not ic[1].ended)
    for i, c in ordered:
        r.apply_role(r.add_role_claim(i, c))

    for i, note in enumerate(result.unreadable_notes):
        q = Question(
            id=stable_id("q", doc_id, "unreadable", i),
            kind="unreadable",
            summary=redact_ssns(note),
            raised_by=doc_id,
        )
        state.questions[q.id] = q
    return [q for q in state.questions if q not in before]

