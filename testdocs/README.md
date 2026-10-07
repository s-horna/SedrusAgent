# Ledgerline test documents: the Bradley household

These are synthetic test documents modelled on the held-out Smith set (`Downloads/SedrusDocs`). The household is a different family, but the document types, layouts, scan quality and traps are the same kinds, and the set tests only behaviors the held-out set presents. Every person, account, SSN (all use the never-issued `666` area number), EIN and amount is invented. Statements have a small "TEST DOCUMENT" footer, and legal documents have a SPECIMEN footer.

Don't ingest `testdocs/` as a whole. This README is a `.md` file, and the pipeline would ingest it. Point the agent at `docs/core` instead.

```
ledgerline ingest testdocs/docs/core
ledgerline entities
```

## How the documents map to the held-out set

| Held-out (Smith) | Test (Bradley) `docs/core/` | Format |
|---|---|---|
| Smith_Children_Irrevocable_Trust_Agreement.pdf | Bradley_Descendants_Irrevocable_Trust_Agreement.pdf | born-digital, 10 pp |
| GS Smith Children Irrev Trust.pdf | JPM Bradley Descendants Irrev Trust.pdf | scanned landscape, corrupted OCR layer, "of 20" but 16 pp, blank pages |
| GS Smith Stmt.pdf (Smith Investment Company, LP) | JPM Bradley Capital Stmt.pdf (Bradley Capital Partners, LP) | scanned, corrupted OCR layer |
| RJ John Smith Roth x0832.pdf | Schwab Robert Bradley Roth x2290.pdf | scanned, corrupted OCR layer, filename/account mismatch |
| RJ Smith JTWROS.pdf | Schwab Bradley JTWROS.pdf | printed-to-PDF, suffix dropped in registration |
| Smith UBS JTWROS.pdf | Bradley Morgan Stanley JTWROS.pdf | vector, consolidated multi-account, registration printed as `Il` for `II` |
| ComputerShare - Exxon.pdf | Equiniti - Carolina Power & Gas.pdf | DRIP; page 3 image-only, "Page 1 of 4" with 3 pages |
| TEST Family 1040.pdf | TEST Bradley Family 1040.pdf | page 1 of a 1040, malformed dependent SSN |

## The household (answer key in brief)

- **Robert W. Bradley II** (SSN …2087) and **Catherine M. Bradley** (SSN …3312) are married and live at 4410 Quail Hollow Rd, Charlotte NC.
- They have three children, all dependents on the 1040: Henry R. (2003‑05‑09, SSN …5521), Olivia C. (2006‑10‑30, SSN …0145) and Samuel T. (2010‑01‑17; his SSN on the 1040 is malformed).
- **The Bradley Descendants Irrevocable Trust** is dated **2020‑06‑03** (EIN …9042).
  - Grantors: Robert and Catherine.
  - Trustee: **Rebecca L. Bradley**, at *410* Quail Hollow Rd.
  - Successor trustee: **Daniel P. Whitaker**. After him, a bank or trust company may be appointed (none is named).
  - Beneficiaries: the three children.
  - Schedule A: 1,500 shares of Quail Hollow Holdings, Inc., and the J.P. Morgan custodial account.
- **Bradley Capital Partners, LP** holds a J.P. Morgan account. No document says who owns it.
- **10 accounts:**
  - J.P. Morgan: trust ×3 (…7310 summary, …7328 brokerage, …7336) and LP …7402.
  - Schwab: Roth …8820 (Robert) and JTWROS …0094.
  - Morgan Stanley JTWROS: …7118, …1118, …3118.
  - Equiniti: DSPP …7220 (Robert).

The full expected state, including expected questions and a `must_not` list, is in `expected/household.json`.

## Gold extractions (`expected/core/<file>.json`)

There is one file per document. Each is a valid `ledgerline.extract.ExtractionResult`: pydantic ignores the extra `_`-prefixed keys. You can use them three ways:

- Feed them to a `FakeExtractor` to test the resolver without model calls.
- Diff a live extraction against them to score the model and prompt.
- Read `_traps` and `_expected_questions` to see what each document is testing.

Every gold quote is checked verbatim against the text actually drawn on the cited page. `build.py` fails if any quote is wrong. `_text_layer` records how many gold quotes can be found in the file's extractable text, using the same case- and punctuation-tolerant match as `quote_in_text`. Low numbers on scanned files are deliberate.

The gold files follow the schema conventions in `ledgerline/extract.py` as of 2026‑10‑06:

- An account's titled owner is `owner`.
- Accounts are named `<Custodian> <type> ...<last4>`.
- Custodian identifiers are short names: `J.P. Morgan`, `Schwab`, `Morgan Stanley`, `Equiniti`.
- Anything the schema can't express goes in `unreadable_notes`.

If the schema changes, update `generator/gold.py` and rebuild.

## Traps to watch for

Each `_traps` list has the details. These are the important ones:

1. **Trust date conflict.** The J.P. Morgan registration says `U/A DTD 09/14/2016`, but the agreement says 2020‑06‑03. This must become a conflict question, not a second trust.
2. **R. Bradley collisions.** Robert W. Bradley II and Rebecca L. Bradley are different people. There is also an `II`/`Il` suffix variant and a registration with the suffix dropped. Morgan Stanley really prints `Il` (it isn't an OCR error), and a model that copies it faithfully gets a second, silent Robert, because `_names_resemble` sees no likeness between `il` and `ii`.
3. **Suffix in the surname slot.** `_names_resemble` takes the last token as the surname, so for "Robert W Bradley II" that token is `ii`. A last-name-first name like "BRADLEY II, ROBERT W" is not seen as similar at all.
4. **OCR text layers that disagree with the image.** Examples: `USO`, `Dct`, `NUM8ER`. A strict quote check rejects correct quotes; the check must tolerate OCR noise but still reject wrong numbers.
5. **Last4 of masked numbers.** `XXX-X7731-0` gives `7310`, but a live model read it as `7731`. Morgan Stanley also misprints one account number once (`228-104474-118` for `228-104477-118`).
6. **Non-entities.** Custodians (`CHARLES SCHWAB & CO INC CUST`) and the share issuer (Carolina Power & Gas) are not household entities.
7. **No evidence of ownership.** The LP statement names no owner, and the LP's address isn't the family's.
8. **Negative statements.** "Neither Grantor shall serve as Trustee".
9. **Partial documents.** Pages 17–20 of 20 are missing, page 4 of 4 is missing, and some pages are blank.

## Checks already run

- **Gold replay through the current pipeline** (perfect extractions, no model). All 8 gold files validate and every gold quote verifies. The replay gives one trust with a trust-date conflict question (trap 1), 10 accounts, and Rebecca offered as a duplicate candidate for "ROBERT W BRADLEY" (trap 2).
- **Live run** of all of `docs/core` with `google/gemini-3.8-flash` (key from `.env`): 7 people, 1 trust, 2 companies, 10 accounts, no full SSNs stored, and the date conflict, missing pages, malformed SSN and Morgan Stanley typo all raised as questions. One deviation: the J.P. Morgan trust sub-accounts came back as last4 `7732`/`7733` instead of `7328`/`7336` (trap 5).

## Rebuilding

```
python -m venv .genvenv && .genvenv/Scripts/pip install -r testdocs/generator/requirements.txt
.genvenv/Scripts/python testdocs/generator/build.py
```

The build is deterministic: seeded scan noise, skew and OCR errors. It rewrites `docs/core` and the gold JSON. `expected/household.json` is written by hand and is kept. Generator layout:

- `facts.py`: the single source of truth for the household.
- `legal.py`: the trust agreement.
- `statements.py`: custodian and transfer-agent statements.
- `form1040.py`: the 1040 page.
- `common.py`: scan and OCR-corruption effects.
- `gold.py`: the answer key.
