"""Build the Bradley household test documents and their gold extractions.

    python build.py            # writes ../docs/** and ../expected/**

Requires: reportlab, pymupdf, pillow (see requirements.txt). Deterministic
seeds are used for every degradation, so rebuilds produce the same pages.
"""

from __future__ import annotations

import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

import pymupdf

sys.path.insert(0, str(Path(__file__).parent))

import form1040  # noqa: E402
import legal  # noqa: E402
import statements as st  # noqa: E402
from common import TextLog, fixed_metadata, norm, scanify  # noqa: E402
from gold import GOLD  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
EXPECTED = ROOT / "expected"


def build() -> dict[str, TextLog]:
    logs: dict[str, TextLog] = {}
    tmp = Path(tempfile.mkdtemp(prefix="ledgerline_testdocs_"))
    (DOCS / "core").mkdir(parents=True, exist_ok=True)

    def out(rel: str) -> Path:
        return DOCS / rel

    # ---- core: born-digital trust agreement
    rel = "core/Bradley_Descendants_Irrevocable_Trust_Agreement.pdf"
    logs[rel] = legal.build_trust_agreement(out(rel))
    fixed_metadata(out(rel), "ReportLab PDF Library - www.reportlab.com")

    # ---- core: scanned J.P. Morgan statements
    for rel, fn, seed in [("core/JPM Bradley Descendants Irrev Trust.pdf", st.build_jpm_trust, "jpm-trust"),
                          ("core/JPM Bradley Capital Stmt.pdf", st.build_jpm_lp, "jpm-lp")]:
        raw = tmp / f"{seed}.pdf"
        logs[rel] = fn(raw)
        scanify(raw, out(rel), seed=seed, dpi=150, skew_range=0.5, ocr="corrupt", ocr_rate=0.07)

    # ---- core: scanned Schwab Roth
    rel = "core/Schwab Robert Bradley Roth x2290.pdf"
    raw = tmp / "roth.pdf"
    logs[rel] = st.build_schwab_roth(raw)
    scanify(raw, out(rel), seed="roth", dpi=150, skew_range=0.8, ocr="corrupt", ocr_rate=0.05)

    # ---- core: printed-to-PDF Schwab joint (vector)
    rel = "core/Schwab Bradley JTWROS.pdf"
    logs[rel] = st.build_schwab_joint(out(rel))
    fixed_metadata(out(rel), "Microsoft: Print To PDF")

    # ---- core: Morgan Stanley consolidated (vector, registration printed with 'Il')
    rel = "core/Bradley Morgan Stanley JTWROS.pdf"
    logs[rel] = st.build_morgan_stanley(out(rel))
    fixed_metadata(out(rel), "macOS Version 14.5 (Build 23F79) Quartz PDFContext")

    # ---- core: Equiniti DRIP - pages 1-2 text, page 3 (privacy notice) image only
    rel = "core/Equiniti - Carolina Power & Gas.pdf"
    raw = tmp / "equiniti.pdf"
    logs[rel] = st.build_equiniti(raw)
    scanify(raw, out(rel), seed="equiniti", dpi=150, skew_range=0.4, ocr="none", text_pages={1, 2})

    # ---- core: 1040
    rel = "core/TEST Bradley Family 1040.pdf"
    logs[rel] = form1040.build_1040(out(rel))
    fixed_metadata(out(rel), "Microsoft: Print To PDF")

    shutil.rmtree(tmp, ignore_errors=True)
    return logs


def extract_text_layer(path: Path) -> dict[int, str]:
    if path.suffix.lower() != ".pdf":
        return {}
    with pymupdf.open(path) as doc:
        return {i: norm(p.get_text()) for i, p in enumerate(doc, start=1)}


def _fragments(quote: str) -> list[str]:
    """Split an elided quote ("A ... B") into its verbatim parts."""
    return [f for f in (norm(x) for x in re.split(r"\.{3}|…", quote)) if f]


def _contains_in_order(text: str, fragments: list[str]) -> bool:
    pos = 0
    for frag in fragments:
        pos = text.find(frag, pos)
        if pos < 0:
            return False
        pos += len(frag)
    return bool(fragments)


def verify(logs: dict[str, TextLog]) -> list[str]:
    """Every gold quote must appear verbatim on the page it cites (in the drawn text).

    An elided quote ("A ... B") passes when each part appears verbatim, in order.
    """
    errors: list[str] = []
    for rel, gold in GOLD.items():
        log = logs.get(rel)
        if log is None:
            errors.append(f"{rel}: no build log")
            continue
        items = [("mention " + x["ref"], x) for x in gold["mentions"]] + \
                [(f"claim {x['subject_ref']}-{x['role']}-{x['object_ref']}", x) for x in gold["claims"]]
        for label, it in items:
            q = norm(it["quote"])
            frags = _fragments(it["quote"])
            page = it.get("page")
            if page and _contains_in_order(log.page_text(page), frags):
                continue
            found = [p for p in log.pages if _contains_in_order(log.page_text(p), frags)]
            if found:
                errors.append(f"{rel}: {label} quote is on page(s) {found}, gold says {page}: {q[:70]!r}")
            else:
                errors.append(f"{rel}: {label} quote not found anywhere: {q[:90]!r}")
    return errors


def _alnum(s: str) -> str:
    # Same tolerance as ledgerline.normalize.quote_in_text: case, spacing and punctuation ignored.
    return re.sub(r"[^a-z0-9]", "", s.lower())


def quote_coverage(logs) -> dict[str, dict]:
    """How many gold quotes survive in the file's extractable text layer (informational)."""
    report = {}
    for rel, gold in GOLD.items():
        layer = extract_text_layer(DOCS / rel)
        quotes = [x["quote"] for x in gold["mentions"] + gold["claims"]]
        if not layer:
            report[rel] = {"text_layer": False, "quotes_in_text_layer": 0, "quotes": len(quotes)}
            continue
        alltext = _alnum(" ".join(layer.values()))
        hit = sum(1 for q in quotes
                  if _contains_in_order(alltext, [f for f in map(_alnum, _fragments(q)) if f]))
        report[rel] = {"text_layer": any(layer.values()), "quotes_in_text_layer": hit, "quotes": len(quotes),
                       "pages": len(layer), "pages_without_text": [p for p, t in layer.items() if not t]}
    return report


def write_expected(coverage) -> None:
    if EXPECTED.exists():
        for f in EXPECTED.rglob("*.json"):
            if f.name != "household.json":
                f.unlink()
    for rel, gold in GOLD.items():
        dst = EXPECTED / f"{rel}.json"
        dst.parent.mkdir(parents=True, exist_ok=True)
        payload = {"_file": rel, **gold, "_text_layer": coverage.get(rel)}
        dst.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    logs = build()
    errors = verify(logs)
    coverage = quote_coverage(logs)
    write_expected(coverage)
    for rel in sorted(GOLD):
        c = coverage[rel]
        layer = (f"{c['quotes_in_text_layer']}/{c['quotes']} gold quotes in text layer"
                 if c.get("text_layer") else "no text layer")
        print(f"  {rel:<70} {layer}")
    if errors:
        print(f"\n{len(errors)} gold quote problem(s):")
        for e in errors:
            print("  -", e)
        return 1
    print("\nAll gold quotes verified against the rendered pages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
