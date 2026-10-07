"""Step 2: an LLM reads one document and reports what it says.

The model never sees entity IDs or existing state and makes no merge
decisions. It returns local mentions (m1, m2, ...) and claims about them,
each backed by a verbatim quote.
"""

from __future__ import annotations

import base64
import json
import mimetypes
import os
from datetime import date
from pathlib import Path
from typing import Literal, Protocol

from pydantic import BaseModel, Field, field_validator

from ledgerline.normalize import normalize_identifiers, parse_date
from ledgerline.state import EntityKind

DEFAULT_MODEL = "google/gemini-3.8-flash"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

DocType = Literal[
    "trust_agreement",
    "trust_amendment",
    "custodian_statement",
    "account_application",
    "tax_return",
    "operating_agreement",
    "power_of_attorney",
    "other",
]

RoleName = Literal[
    "grantor",
    "trustee",
    "successor_trustee",
    "beneficiary",
    "owner",
    "authorized_signer",
    "power_of_attorney",
    "member",
    "manager",
    "spouse_of",
    "child_of",
]


class Mention(BaseModel):
    ref: str = Field(description="Local reference, e.g. m1. Unique within this document.")
    kind: EntityKind
    name: str = Field(description="Name exactly as written in the document.")
    identifiers: dict[str, str] = Field(
        default_factory=dict,
        description="Only values printed in the document: ssn_last4, dob, ein_last4, "
        "account_last4, custodian, trust_date. Write dates as YYYY-MM-DD and last4 values "
        "as exactly 4 digits.",
    )
    page: int | None = None
    quote: str = Field(description="Verbatim text where this party is introduced.")

    _ids = field_validator("identifiers")(lambda v: normalize_identifiers(v))


class ExtractedClaim(BaseModel):
    subject_ref: str
    role: RoleName
    object_ref: str
    qualifiers: dict[str, str] = Field(default_factory=dict)
    ended: bool = Field(
        default=False,
        description="True only when the document states this role ENDS "
        "(resignation, removal, death, closure).",
    )
    effective_from: date | None = None
    effective_to: date | None = None
    page: int | None = None
    quote: str = Field(description="Verbatim text that establishes (or ends) this role.")

    _dates = field_validator("effective_from", "effective_to", mode="before")(parse_date)


class ExtractionResult(BaseModel):
    doc_type: DocType
    doc_date: date | None = None
    mentions: list[Mention] = Field(default_factory=list)
    claims: list[ExtractedClaim] = Field(default_factory=list)
    unreadable_notes: list[str] = Field(
        default_factory=list,
        description="Anything relevant you could not read or interpret with confidence.",
    )

    _date = field_validator("doc_date", mode="before")(parse_date)


class Extractor(Protocol):
    model: str

    def extract(self, path: Path) -> ExtractionResult: ...


SYSTEM_PROMPT = """You read financial and legal documents for a wealth management firm \
and report the people, trusts, companies and accounts they mention, and the roles \
that connect them.

Rules:
- Report only what the document states. Never infer or fill in missing values.
- Every mention and claim must include a verbatim quote copied from the document.
- Distinguish carefully: trustee vs successor_trustee, owner vs beneficiary.
- An account's titled owner (a person, trust or company) is its `owner`. A trustee
  named in an account title ("JANE DOE TTEE") is `trustee` of the trust, not of the account.
- When a document removes someone from a role (resignation, removal, replacement),
  emit a claim for that person and role with ended=true, plus a claim for the new holder.
- Relationship roles read left to right: subject child_of object, subject spouse_of object.
- Custodians, banks, law firms and other service providers are NOT entities. Record the
  custodian only as the `custodian` identifier on the account it holds.
- For the `custodian` identifier use the firm's short name, e.g. "Schwab", "Fidelity",
  "J.P. Morgan" (not "Charles Schwab & Co., Inc." or "J.P. Morgan Securities LLC").
- Name accounts "<Custodian> <account type> ...<last4>", e.g. "Schwab Trust Brokerage ...9012".
- `account_last4` is the last 4 digits of the account number as printed, counting every
  digit including any trailing check digit after a hyphen and ignoring masking characters:
  "123-45678-9" and "XXX-X5678-9" both give "6789".
- When a document lists property held by a trust, person or company (e.g. shares of a
  company on a trust's schedule of assets), emit an `owner` claim for that holding.
- Give each person their full name as written in the most complete form in the document.
- Never copy a full Social Security number into a quote or note; elide it with "...",
  e.g. "JANE A DOE ... DAUGHTER". Record ssn_last4 only when the SSN is printed with
  exactly 9 digits; a malformed SSN goes in unreadable_notes without the number.
- If something is illegible or ambiguous, describe it in unreadable_notes instead of guessing.
  Also note there: pages missing from the document (the page numbering says "of N" but
  fewer pages are present), and an account number printed differently in different places
  of the same document.
- Return JSON matching the provided schema."""


def _content_part(path: Path) -> dict:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    if mime.startswith("text/"):
        return {"type": "text", "text": path.read_text(encoding="utf-8")}
    data_url = f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"
    if mime.startswith("image/"):
        return {"type": "image_url", "image_url": {"url": data_url}}
    return {"type": "file", "file": {"filename": path.name, "file_data": data_url}}


class OpenRouterExtractor:
    def __init__(self, model: str | None = None, api_key: str | None = None):
        from openai import OpenAI

        self.model = model or os.environ.get("LEDGERLINE_MODEL", DEFAULT_MODEL)
        key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not key:
            raise RuntimeError("OPENROUTER_API_KEY is not set")
        self.client = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=key)

    def extract(self, path: Path) -> ExtractionResult:
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Document filename: {path.name}"},
                        _content_part(path),
                    ],
                },
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "extraction",
                    "schema": ExtractionResult.model_json_schema(),
                },
            },
        )
        content = response.choices[0].message.content or ""
        return ExtractionResult.model_validate(json.loads(content))
