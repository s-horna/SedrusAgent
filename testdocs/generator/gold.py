"""Gold extractions: what a perfect extractor should return for each document.

Each entry is ExtractionResult-compatible (ledgerline.extract.ExtractionResult)
plus underscore-prefixed annotation keys that pydantic ignores:

  _file                  document path relative to testdocs/docs
  _format                how the file was produced (born-digital, scanned+OCR, image-only)
  _traps                 what makes this document hard
  _expected_questions    what a careful agent should put in front of a human

Conventions
- `name` is the name as printed (the visual reading for image docs).
- `custodian` identifiers are canonical short names so the same account
  matches across documents: J.P. Morgan, Schwab, Morgan Stanley, Equiniti.
- `account_last4` is the last 4 DIGITS of the printed number (letters/dashes dropped).
- An account's titled owner (person, trust or company) is its `owner`
  (ledgerline.extract SYSTEM_PROMPT); ownership interests in companies are also
  `owner`; IRA designations use `beneficiary` with qualifiers {designation, share}.
- Accounts are named "<Custodian> <account type> ...<last4>".
- Things the schema cannot express (no matching role, illegible values) go in
  unreadable_notes, which the pipeline turns into questions.
- Every quote is verified verbatim against the text drawn on that page
  (build.py fails otherwise). An elided quote ("A ... B") passes when each part
  is verbatim and in order; use it to keep full SSNs out of quotes, which the
  pipeline stores. For scanned docs the OCR text layer is corrupted
  on purpose, so quotes will NOT always match the extractable text there.
"""

from __future__ import annotations


def m(ref, kind, name, quote, page, **ids):
    return {"ref": ref, "kind": kind, "name": name, "identifiers": ids, "page": page, "quote": quote}


def cl(subj, role, obj, quote, page, effective_from=None, effective_to=None, ended=False, **q):
    d = {"subject_ref": subj, "role": role, "object_ref": obj, "qualifiers": q, "page": page, "quote": quote}
    if ended:
        d["ended"] = True
    if effective_from:
        d["effective_from"] = effective_from
    if effective_to:
        d["effective_to"] = effective_to
    return d


JPM, SCHWAB, MS, EQ = "J.P. Morgan", "Schwab", "Morgan Stanley", "Equiniti"

GOLD: dict[str, dict] = {}

# ============================================================== core: trust agreement
_pre = ("by and between ROBERT W. BRADLEY II and CATHERINE M. BRADLEY, husband and wife")
GOLD["core/Bradley_Descendants_Irrevocable_Trust_Agreement.pdf"] = {
    "_format": "born-digital (text layer, 10 pages, law-firm style)",
    "doc_type": "trust_agreement",
    "doc_date": "2020-06-03",
    "mentions": [
        m("m1", "person", "ROBERT W. BRADLEY II", _pre, 2),
        m("m2", "person", "CATHERINE M. BRADLEY", _pre, 2),
        m("m3", "trust", "THE BRADLEY DESCENDANTS IRREVOCABLE TRUST",
          "to be known as THE BRADLEY DESCENDANTS IRREVOCABLE TRUST (the \"Trust\")", 2,
          trust_date="2020-06-03", ein_last4="9042"),
        m("m4", "person", "REBECCA L. BRADLEY",
          "and REBECCA L. BRADLEY, of Mecklenburg County, North Carolina (the \"Trustee\")", 2),
        m("m5", "person", "HENRY R. BRADLEY", "HENRY R. BRADLEY, born May 9, 2003", 2, dob="2003-05-09"),
        m("m6", "person", "OLIVIA C. BRADLEY", "OLIVIA C. BRADLEY, born October 30, 2006", 2, dob="2006-10-30"),
        m("m7", "person", "SAMUEL T. BRADLEY", "SAMUEL T. BRADLEY, born January 17, 2010", 2, dob="2010-01-17"),
        m("m8", "person", "DANIEL P. WHITAKER", "DANIEL P. WHITAKER shall serve as successor Trustee", 5),
        m("m9", "account", "J.P. Morgan Trust Portfolio ...7310",
          "Custodial account established with J.P. Morgan Securities LLC, Account No. XXX-X7731-0, in the name of "
          "the Bradley Descendants Irrevocable Trust", 10, custodian=JPM, account_last4="7310"),
        m("m10", "company", "Quail Hollow Holdings, Inc.",
          "1,500 shares of common stock, Quail Hollow Holdings, Inc.", 10),
    ],
    "claims": [
        cl("m1", "grantor", "m3", _pre + ", each residing in Mecklenburg County, North Carolina (each a \"Grantor\"", 2),
        cl("m2", "grantor", "m3", _pre + ", each residing in Mecklenburg County, North Carolina (each a \"Grantor\"", 2),
        cl("m1", "spouse_of", "m2", _pre, 2),
        cl("m4", "trustee", "m3", "REBECCA L. BRADLEY shall serve as the initial Trustee of the Trust", 5),
        cl("m8", "successor_trustee", "m3",
           "If REBECCA L. BRADLEY dies, resigns, becomes incapacitated or otherwise ceases to serve, DANIEL P. "
           "WHITAKER shall serve as successor Trustee", 5),
        cl("m5", "beneficiary", "m3", "the Children are HENRY R. BRADLEY, OLIVIA C. BRADLEY and SAMUEL T. BRADLEY", 3),
        cl("m6", "beneficiary", "m3", "the Children are HENRY R. BRADLEY, OLIVIA C. BRADLEY and SAMUEL T. BRADLEY", 3),
        cl("m7", "beneficiary", "m3", "the Children are HENRY R. BRADLEY, OLIVIA C. BRADLEY and SAMUEL T. BRADLEY", 3),
        *[cl(c, "child_of", p, "The Grantors are the parents of three (3) children", 2)
          for c in ("m5", "m6", "m7") for p in ("m1", "m2")],
        cl("m3", "owner", "m9",
           "Account No. XXX-X7731-0, in the name of the Bradley Descendants Irrevocable Trust", 10),
        cl("m3", "owner", "m10", "1,500 shares of common stock, Quail Hollow Holdings, Inc.", 10, shares="1,500"),
    ],
    "unreadable_notes": [],
    "_traps": [
        "Section 2.2 says 'Neither Grantor shall serve as Trustee' - a negative statement; the grantors must NOT "
        "get trustee roles.",
        "Trustee Rebecca L. Bradley and grantor Robert W. Bradley II are both 'R. Bradley' and live at 410 vs 4410 "
        "Quail Hollow Rd (different ZIPs). Never merge them.",
        "Only one successor is named (Daniel P. Whitaker); after him, a bank or trust company 'may' be appointed. "
        "That generic fallback names no entity and must not become one.",
        "Schedule A links the trust to a company (1,500 shares of Quail Hollow Holdings, Inc.) and to the J.P. "
        "Morgan account; the account number is masked (XXX-X7731-0).",
        "Cover page and body both list parties; extract each role once (cover is a summary, body is authoritative).",
    ],
    "_expected_questions": [],
}

# ============================================================== core: JPM trust statement
_reg = "BRADLEY DESCENDANTS IRREVOCABLE TRUST U/A DTD 09/14/2016 REBECCA L. BRADLEY, TRUSTEE"
GOLD["core/JPM Bradley Descendants Irrev Trust.pdf"] = {
    "_format": "scanned landscape statement, corrupted OCR text layer; printed 'Page n of 20' but only pages 1-16 "
               "present; pages 6 and 10 blank",
    "doc_type": "custodian_statement",
    "doc_date": "2025-10-31",
    "mentions": [
        m("m1", "trust", "BRADLEY DESCENDANTS IRREVOCABLE TRUST", _reg, 7, trust_date="2016-09-14"),
        m("m2", "person", "REBECCA L. BRADLEY", _reg, 7),
        m("m3", "account", "J.P. Morgan Trust Portfolio ...7310",
          "PORTFOLIO NUMBER : 448-17731-0", 2, custodian=JPM, account_last4="7310"),
        m("m4", "account", "J.P. Morgan Trust Brokerage ...7328",
          "BRADLEY DESCENDANTS IRREV TR BRKG 448-17732-8", 2, custodian=JPM, account_last4="7328"),
        m("m5", "account", "J.P. Morgan Trust Portfolio ...7336",
          "BRADLEY DESCENDANTS IRREV TR 448-17733-6", 2, custodian=JPM, account_last4="7336"),
    ],
    "claims": [
        cl("m2", "trustee", "m1", _reg, 7),
        cl("m1", "owner", "m3", "BRADLEY DESCENDANTS IRREVOCABLE TRUST", 1),
        cl("m1", "owner", "m4", _reg, 7),
        cl("m1", "owner", "m5", _reg, 11),
    ],
    "unreadable_notes": [
        "Statement shows pages 1-16 of 20; pages 17-20 (bank statement, fees, disclosures) are missing.",
    ],
    "_traps": [
        "CONFLICT: registration says 'U/A DTD 09/14/2016' but the trust agreement is dated June 3, 2020. Same "
        "trust name, different trust_date. The skeleton's resolver treats a differing trust_date as 'provably "
        "different' and would silently create a SECOND trust - the correct outcome is a conflict question.",
        "Mailed to 'REBECCA L. BRADLEY, 410 Quail Hollow RD' - the addressee is the trustee, not an account holder.",
        "Consolidated summary portfolio (448-17731-0, shown masked as XXX-X7731-0 in the footer) plus two "
        "sub-accounts; the zero-balance BRKG sub-account is still an account.",
        "Masked footer numbers (XXX-X7733-6) vs unmasked numbers on General Information pages. The trailing "
        "'-0/-8/-6' digit makes last4 ambiguous (7310 vs 7731); gold uses the last 4 digits of the full string.",
        "OCR layer has errors (USO for USD, Dct for Oct, (Lossl ...).",
    ],
    "_expected_questions": [
        {"kind": "conflict", "about": "Trust date 2016-09-14 (custodian registration) vs 2020-06-03 (trust "
         "agreement) for the Bradley Descendants Irrevocable Trust."},
        {"kind": "unreadable", "about": "Pages 17-20 of 20 missing."},
    ],
}

# ============================================================== core: JPM LP statement
GOLD["core/JPM Bradley Capital Stmt.pdf"] = {
    "_format": "scanned landscape statement, corrupted OCR text layer, 8 pages",
    "doc_type": "custodian_statement",
    "doc_date": "2025-10-31",
    "mentions": [
        m("m1", "company", "BRADLEY CAPITAL PARTNERS, LP", "BRADLEY CAPITAL PARTNERS, LP 200 S TRYON ST STE 1450", 1),
        m("m2", "account", "J.P. Morgan Partnership Portfolio ...7402", "PORTFOLIO NUMBER : 448-17740-2", 2,
          custodian=JPM, account_last4="7402"),
    ],
    "claims": [
        cl("m1", "owner", "m2", "BRADLEY CAPITAL PARTNERS, LP", 1),
    ],
    "unreadable_notes": [],
    "_traps": [
        "Nothing in this document says who owns or controls the partnership, and its address (200 S Tryon St) is "
        "not the family's. From this document alone the company must NOT be attached to any person.",
        "The same advisor team and template as the trust statement - shared boilerplate is not evidence of "
        "common ownership.",
        "Header title is truncated to 'BRADLEY CAPITAL PARTNERS' (no ', LP').",
    ],
    "_expected_questions": [],
}

# ============================================================== core: Schwab Roth
GOLD["core/Schwab Robert Bradley Roth x2290.pdf"] = {
    "_format": "scanned portrait statement, corrupted OCR text layer, 8 pages (6 boilerplate)",
    "doc_type": "custodian_statement",
    "doc_date": "2025-09-30",
    "mentions": [
        m("m1", "person", "ROBERT W BRADLEY II", "ROBERT W BRADLEY II CHARLES SCHWAB & CO INC CUST ROTH CONTRIBUTORY IRA", 1),
        m("m2", "account", "Schwab Roth IRA ...8820", "Bradley II, Robert - Roth IRA Account Summary - #4471-8820", 1,
          custodian=SCHWAB, account_last4="8820"),
        m("m3", "person", "Catherine M Bradley", "Primary Beneficiaries: Catherine M Bradley (100.00%)", 2),
        m("m4", "person", "Henry R Bradley", "Contingent Beneficiaries: Henry R Bradley (33.34%)", 2),
        m("m5", "person", "Olivia C Bradley", "Olivia C Bradley (33.33%)", 2),
        m("m6", "person", "Samuel T Bradley", "Samuel T Bradley (33.33%)", 2),
    ],
    "claims": [
        cl("m1", "owner", "m2", "ROBERT W BRADLEY II CHARLES SCHWAB & CO INC CUST ROTH CONTRIBUTORY IRA", 1,
           account_type="Roth IRA"),
        cl("m3", "beneficiary", "m2", "Primary Beneficiaries: Catherine M Bradley (100.00%)", 2,
           designation="primary", share="100.00%"),
        cl("m4", "beneficiary", "m2", "Contingent Beneficiaries: Henry R Bradley (33.34%)", 2,
           designation="contingent", share="33.34%"),
        cl("m5", "beneficiary", "m2", "Olivia C Bradley (33.33%)", 2, designation="contingent", share="33.33%"),
        cl("m6", "beneficiary", "m2", "Samuel T Bradley (33.33%)", 2, designation="contingent", share="33.33%"),
    ],
    "unreadable_notes": [],
    "_traps": [
        "Filename says x2290 but the account number is 4471-8820 - trust the document, not the filename.",
        "'CHARLES SCHWAB & CO INC CUST' is the IRA custodian, not a household company and not an account holder.",
        "Beneficiaries (owner vs beneficiary distinction) - the spouse is a beneficiary, not a holder.",
        "Noise: 'State (SC) Withholding Election' although the client lives in NC.",
        "Name formats: 'ROBERT W BRADLEY II' and 'Bradley II, Robert' (last-name-first, no middle initial).",
    ],
    "_expected_questions": [],
}

# ============================================================== core: Schwab joint
_joint = "ROBERT W BRADLEY & CATHERINE M BRADLEY JT TEN"
GOLD["core/Schwab Bradley JTWROS.pdf"] = {
    "_format": "printed-to-PDF statement (vector text layer), 6 pages",
    "doc_type": "custodian_statement",
    "doc_date": "2025-10-31",
    "mentions": [
        m("m1", "person", "ROBERT W BRADLEY", _joint, 1),
        m("m2", "person", "CATHERINE M BRADLEY", _joint, 1),
        m("m3", "account", "Schwab JTWROS Brokerage ...0094",
          "BRADLEY II, ROBERT W & BRADLEY, CATHERINE M - JTWROS Account Summary - #6612-0094", 1,
          custodian=SCHWAB, account_last4="0094"),
    ],
    "claims": [
        cl("m1", "owner", "m3", _joint, 1, ownership="JTWROS"),
        cl("m2", "owner", "m3", _joint, 1, ownership="JTWROS"),
    ],
    "unreadable_notes": [],
    "_traps": [
        "Registration drops the 'II' suffix ('ROBERT W BRADLEY') while the summary title keeps it "
        "('BRADLEY II, ROBERT W'). Name-only evidence: same person as Robert W. Bradley II, but no identifier "
        "proves it - expect a possible_duplicate question (or a justified link), never a silent new person.",
        "Last-name-first title 'BRADLEY II, ROBERT W': if an extractor uses that as the name, a surname/first-"
        "initial similarity check compares 'w' to 'ii' and finds no resemblance - the person gets silently "
        "duplicated. Normalize 'LAST, FIRST' before comparing.",
        "Address is wrapped mid-street across lines ('JT TEN 4410 QUAIL HOLLOW' / 'RD CHARLOTTE 28210').",
        "'JT TEN' = joint tenants (JTWROS) - both people are holders.",
    ],
    "_expected_questions": [
        {"kind": "possible_duplicate", "about": "'ROBERT W BRADLEY' vs Robert W. Bradley II (no identifiers)."},
        {"kind": "possible_duplicate", "about": "'CATHERINE M BRADLEY' vs Catherine M. Bradley (no identifiers)."},
    ],
}

# ============================================================== core: Morgan Stanley
_ms_reg = "Robert W Bradley Il Catherine M Bradley JTWROS"
GOLD["core/Bradley Morgan Stanley JTWROS.pdf"] = {
    "_format": "vector PDF (text layer) with a multi-section structure: 6-page consolidated summary, then "
               "account statements with their own 'Page x of y' numbering (Active Assets 1-6, Select UMA 1-4)",
    "doc_type": "custodian_statement",
    "doc_date": "2025-10-31",
    "mentions": [
        m("m1", "person", "Robert W Bradley II", _ms_reg, 1),
        m("m2", "person", "Catherine M Bradley", _ms_reg, 1),
        m("m3", "account", "Morgan Stanley Active Assets ...7118",
          "228-104477-118 Active Assets Account - Brokerage", 5, custodian=MS, account_last4="7118"),
        m("m4", "account", "Morgan Stanley Select UMA ...1118",
          "228-104491-118 Portfolio Management - Select UMA - Advisory", 5, custodian=MS, account_last4="1118"),
        m("m5", "account", "Morgan Stanley Alternative Investments ...3118",
          "228-104503-118 Alternative Investments - Brokerage", 5, custodian=MS, account_last4="3118"),
    ],
    "claims": [
        *[cl(p, "owner", a, _ms_reg, 1, ownership="JTWROS") for a in ("m3", "m4", "m5") for p in ("m1", "m2")],
    ],
    "unreadable_notes": [
        "Account number for the Active Assets account is printed as 228-104474-118 in the 'Change in the value of "
        "your accounts' table (page 5 of the summary) but 228-104477-118 everywhere else.",
    ],
    "_traps": [
        "The registration is PRINTED as 'Robert W Bradley Il' (lower-case L): the drawn glyphs and the text layer "
        "agree, and the 'l' is only slightly taller than an 'I'. This is not an OCR error. The gold deliberately "
        "names him 'Robert W Bradley II' (the suffix intended) while its quotes keep the printed 'Il'.",
        "An extractor that copies the name faithfully ('Robert W Bradley Il') gets no match: 'il' is neither "
        "equal to 'ii' nor a substring of it, and the surname check compares 'il' with 'ii'. _names_resemble "
        "returns False and a second Robert is created silently, with no question.",
        "Typo account number 228-104474-118 (last4 4118) matches no account: it is the Active Assets account "
        "misprinted, not a fourth account.",
        "Three accounts sharing the same suffix (-118); last4 values are 7118 / 1118 / 3118.",
        "Page numbering restarts per section (Page 1 of 6, then Page 1 of 6, then Page 1 of 4); page 2 is blank.",
        "The Alternatives account has no account-level section; its registration comes only from the "
        "consolidated summary.",
    ],
    "_expected_questions": [
        {"kind": "unreadable", "about": "Account number typo 228-104474-118 vs 228-104477-118."},
        {"kind": "possible_duplicate", "about": "'Robert W Bradley II' / 'Catherine M Bradley' vs existing people "
         "(name-only)."},
    ],
}

# ============================================================== core: Equiniti DRIP
_eq = "ROBERT W BRADLEY II 4410 QUAIL HOLLOW RD"
GOLD["core/Equiniti - Carolina Power & Gas.pdf"] = {
    "_format": "transfer-agent DSPP statement; pages 1-2 have text, page 3 (privacy notice) is image-only; "
               "printed 'Page 1 of 4' but page 4 missing",
    "doc_type": "custodian_statement",
    "doc_date": "2025-09-15",
    "mentions": [
        m("m1", "person", "ROBERT W BRADLEY II", _eq, 1),
        m("m2", "account", "Equiniti DSPP ...7220", "Holder Account Number C0004417220", 1,
          custodian=EQ, account_last4="7220"),
    ],
    "claims": [
        cl("m1", "owner", "m2", _eq, 1),
    ],
    "unreadable_notes": [
        "Page 4 of 4 is missing.",
    ],
    "_traps": [
        "'Carolina Power & Gas Corporation' is the ISSUER of the shares, not a household company. It must not "
        "become a company entity in the household.",
        "Page 3 has no text layer (boilerplate only).",
    ],
    "_expected_questions": [
        {"kind": "unreadable", "about": "Page 4 of 4 missing."},
    ],
}

# ============================================================== core: 1040
GOLD["core/TEST Bradley Family 1040.pdf"] = {
    "_format": "single page printed from tax software (vector text, Courier entries); page 21 of a larger "
               "return printout",
    "doc_type": "tax_return",
    "doc_date": "2024-12-31",
    "mentions": [
        m("m1", "person", "ROBERT W BRADLEY II", "ROBERT W Last name BRADLEY II", 1, ssn_last4="2087"),
        m("m2", "person", "CATHERINE M BRADLEY", "CATHERINE M Last name BRADLEY", 1, ssn_last4="3312"),
        m("m3", "person", "HENRY R BRADLEY", "HENRY R BRADLEY ... SON", 1, ssn_last4="5521"),
        m("m4", "person", "OLIVIA C BRADLEY", "OLIVIA C BRADLEY ... DAUGHTER", 1, ssn_last4="0145"),
        m("m5", "person", "SAMUEL T BRADLEY", "SAMUEL T BRADLEY ... SON", 1),
    ],
    "claims": [
        cl("m1", "spouse_of", "m2", "Married filing jointly (even if only one had income)", 1),
        cl("m3", "child_of", "m1", "HENRY R BRADLEY ... SON", 1),
        cl("m3", "child_of", "m2", "HENRY R BRADLEY ... SON", 1),
        cl("m4", "child_of", "m1", "OLIVIA C BRADLEY ... DAUGHTER", 1),
        cl("m4", "child_of", "m2", "OLIVIA C BRADLEY ... DAUGHTER", 1),
        cl("m5", "child_of", "m1", "SAMUEL T BRADLEY ... SON", 1),
        cl("m5", "child_of", "m2", "SAMUEL T BRADLEY ... SON", 1),
    ],
    "unreadable_notes": [
        "Dependent SAMUEL T BRADLEY's SSN is printed with 10 digits instead of 9 - malformed; no reliable "
        "ssn_last4.",
    ],
    "_traps": [
        "doc_date: the return is for tax year 2024 (no signature date on this page); 2024-12-31 used as the "
        "as-of date.",
        "SAMUEL T BRADLEY's SSN is malformed (10 digits), so he has no identifier here: name-only evidence.",
        "First name and last name are in separate boxes ('ROBERT W' / 'BRADLEY II'); the suffix sits in the "
        "last-name box.",
        "SSNs are printed in full; only the last 4 should be stored. Quotes are stored too, so the gold quotes "
        "elide the SSN column ('OLIVIA C BRADLEY ... DAUGHTER'); a quote that copies the row verbatim leaks the "
        "full SSN into state.",
    ],
    "_expected_questions": [
        {"kind": "unreadable", "about": "Malformed SSN for SAMUEL T BRADLEY."},
    ],
}
