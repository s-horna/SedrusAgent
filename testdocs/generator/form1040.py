"""Page 1 of a 2024 Form 1040 as printed from tax software (Courier entries)."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import letter

from common import LoggedCanvas, TextLog, fiction_mark

W, H = letter
L, R = 36, W - 36


def _box(c, x, y, w, h, lw=0.5):
    c.setLineWidth(lw)
    c.rect(x, y, w, h)


def _label(c, x, y, s, size=6.2, bold=False):
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    c.drawString(x, y, s)


def _entry(c, x, y, s, size=10, right=False):
    c.setFont("Courier-Bold", size)
    (c.drawRightString if right else c.drawString)(x, y, s)


def _check(c, x, y, checked=False):
    c.setLineWidth(0.5)
    c.rect(x, y, 7, 7)
    if checked:
        c.setFont("Courier-Bold", 9)
        c.drawString(x + 0.6, y + 0.4, "X")


def build_1040(path: Path) -> TextLog:
    log = TextLog()
    c = LoggedCanvas(str(path), log)

    # ---- header
    c.setFont("Helvetica-Bold", 20)
    c.drawString(L + 10, H - 52, "1040")
    c.saveState(); c.translate(L + 4, H - 56); c.rotate(90); c.setFont("Helvetica", 6); c.drawString(0, 0, "Form"); c.restoreState()
    _label(c, L + 70, H - 38, "Department of the Treasury - Internal Revenue Service")
    c.setFont("Helvetica-Bold", 10.5)
    c.drawString(L + 70, H - 54, "U.S. Individual Income Tax Return")
    _box(c, L + 260, H - 60, 52, 24, 1)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(L + 265, H - 54, "2024")
    _label(c, L + 320, H - 50, "OMB No. 1545-0074")
    _label(c, L + 400, H - 50, "IRS Use Only - Do not write or staple in this space.", 5.5)
    c.setLineWidth(1)
    c.line(L, H - 62, R, H - 62)
    _label(c, L, H - 71, "For the year Jan. 1 - Dec. 31, 2024, or other tax year beginning", 6.3)
    _label(c, L + 300, H - 71, ", ending", 6.3)
    _label(c, R - 110, H - 71, "See separate instructions.", 6.3)

    # ---- name / SSN grid
    rows = [
        ("Your first name and middle initial", "ROBERT W", "Last name", "BRADLEY II", "Your social security number",
         ["666", "41", "2087"]),
        ("If joint return, spouse's first name and middle initial", "CATHERINE M", "Last name", "BRADLEY",
         "Spouse's social security number", ["666", "58", "3312"]),
    ]
    y = H - 75
    for lab1, val1, lab2, val2, lab3, ssn in rows:
        c.setLineWidth(0.5)
        c.line(L, y, R, y)
        _label(c, L + 2, y - 7, lab1)
        _entry(c, L + 2, y - 19, val1)
        c.line(L + 215, y, L + 215, y - 23)
        _label(c, L + 217, y - 7, lab2)
        _entry(c, L + 217, y - 19, val2)
        c.line(R - 130, y, R - 130, y - 23)
        _label(c, R - 128, y - 7, lab3, 6, bold=True)
        _entry(c, R - 124, y - 19, "  ".join(ssn))
        y -= 23
    c.line(L, y, R, y)
    _label(c, L + 2, y - 7, "Home address (number and street). If you have a P.O. box, see instructions.")
    _label(c, R - 175, y - 7, "Apt. no.")
    _entry(c, L + 2, y - 19, "4410 QUAIL HOLLOW RD")
    y -= 23
    c.line(L, y, R - 130, y)
    _label(c, L + 2, y - 7, "City, town, or post office. If you have a foreign address, also complete spaces below.")
    _label(c, R - 205, y - 7, "State")
    _label(c, R - 180, y - 7, "ZIP code")
    _entry(c, L + 2, y - 19, "CHARLOTTE")
    _entry(c, R - 205, y - 19, "NC")
    _entry(c, R - 180, y - 19, "28210")
    y -= 23
    c.line(L, y, R - 130, y)
    _label(c, L + 2, y - 7, "Foreign country name")
    _label(c, L + 215, y - 7, "Foreign province/state/county")
    _label(c, R - 205, y - 7, "Foreign postal code")
    _label(c, R - 126, H - 128, "Presidential Election Campaign", 6, bold=True)
    for i, t in enumerate(["Check here if you, or your spouse if filing", "jointly, want $3 to go to this fund.",
                           "Checking a box below will not change", "your tax or refund."]):
        _label(c, R - 126, H - 136 - i * 7, t, 5.4)
    _check(c, R - 100, H - 172); _label(c, R - 90, H - 171, "You"); _check(c, R - 60, H - 172); _label(c, R - 50, H - 171, "Spouse")
    y -= 23
    c.setLineWidth(1)
    c.line(L, y, R, y)

    # ---- filing status
    y -= 12
    _label(c, L, y, "Filing Status", 7.5, bold=True)
    _check(c, L + 70, y - 1); _label(c, L + 80, y, "Single", 7)
    _check(c, L + 300, y - 1); _label(c, L + 310, y, "Head of household (HOH)", 7)
    y -= 10
    _label(c, L, y, "Check only", 6.5)
    _check(c, L + 70, y - 1, True); _label(c, L + 80, y, "Married filing jointly (even if only one had income)", 7)
    _check(c, L + 300, y - 1); _label(c, L + 310, y, "Qualifying surviving spouse (QSS)", 7)
    y -= 10
    _label(c, L, y, "one box.", 6.5)
    _check(c, L + 70, y - 1); _label(c, L + 80, y, "Married filing separately (MFS)", 7)
    y -= 10
    _label(c, L + 70, y, "If you checked the MFS box, enter the name of your spouse. If you checked the HOH or QSS box, "
           "enter the child's name if the qualifying person is", 6)
    _label(c, L + 70, y - 8, "a child but not your dependent:", 6)
    y -= 20
    c.setLineWidth(1)
    c.line(L, y, R, y)
    y -= 10
    _label(c, L, y, "Digital", 7.5, bold=True)
    _label(c, L + 70, y, "At any time during 2024, did you: (a) receive (as a reward, award, or payment for property or "
           "services); or (b) sell,", 6.5)
    _label(c, L, y - 9, "Assets", 7.5, bold=True)
    _label(c, L + 70, y - 9, "exchange, or otherwise dispose of a digital asset (or a financial interest in a digital "
           "asset)? (See instructions.)", 6.5)
    _check(c, R - 70, y - 10); _label(c, R - 60, y - 9, "Yes"); _check(c, R - 38, y - 10, True); _label(c, R - 28, y - 9, "No")
    y -= 18
    c.line(L, y, R, y)
    y -= 10
    _label(c, L, y, "Standard", 7.5, bold=True)
    _label(c, L + 70, y, "Someone can claim:", 6.5, bold=True)
    _check(c, L + 140, y - 1); _label(c, L + 150, y, "You as a dependent", 6.5)
    _check(c, L + 250, y - 1); _label(c, L + 260, y, "Your spouse as a dependent", 6.5)
    _label(c, L, y - 9, "Deduction", 7.5, bold=True)
    _check(c, L + 70, y - 10); _label(c, L + 80, y - 9, "Spouse itemizes on a separate return or you were a dual-status alien", 6.5)
    y -= 18
    c.line(L, y, R, y)
    y -= 10
    _label(c, L, y, "Age/Blindness", 7, bold=True)
    _label(c, L + 60, y, "You:", 6.5, bold=True); _check(c, L + 80, y - 1)
    _label(c, L + 90, y, "Were born before January 2, 1960", 6.3); _check(c, L + 210, y - 1); _label(c, L + 220, y, "Are blind", 6.3)
    _label(c, L + 270, y, "Spouse:", 6.5, bold=True); _check(c, L + 300, y - 1)
    _label(c, L + 310, y, "Was born before January 2, 1960", 6.3); _check(c, L + 440, y - 1); _label(c, L + 450, y, "Is blind", 6.3)
    y -= 6
    c.line(L, y, R, y)

    # ---- dependents
    y -= 9
    _label(c, L, y, "Dependents", 7.5, bold=True)
    _label(c, L + 50, y, "(see instructions):", 6.3)
    _label(c, L + 270, y, "(2) Social security number", 6.3)
    _label(c, L + 362, y, "(3) Relationship to you", 5.6)
    _label(c, R - 108, y, "(4) Check if qualifies for (see instr.):", 4.9)
    y -= 8
    _label(c, L, y, "If more", 6.3)
    _label(c, L + 50, y, "(1) First name", 6.3)
    _label(c, L + 150, y, "Last name", 6.3)
    _label(c, R - 115, y, "Child tax credit", 5.3)
    _label(c, R - 60, y, "Credit for other dependents", 5.0)
    deps = [("HENRY R", "BRADLEY", "666-83-5521", "SON", False, True),
            ("OLIVIA C", "BRADLEY", "666-72-0145", "DAUGHTER", False, True),
            ("SAMUEL T", "BRADLEY", "666-19-44028", "SON", True, False),
            ("", "", "", "", False, False)]
    side = ["than four", "depend-", "ents, see", "instr. and", "check", "here"]
    for i, t in enumerate(side):
        _label(c, L, y - 9 - i * 7, t, 6)
    for i, (fn, ln, ssn, rel, ctc, odc) in enumerate(deps):
        yy = y - 4 - i * 12
        c.setLineWidth(0.4)
        c.line(L + 48, yy - 9, R, yy - 9)
        for xx in (L + 265, L + 365, R - 118, R - 62):
            c.line(xx, yy + 3, xx, yy - 9)
        if fn:
            _entry(c, L + 52, yy - 7, f"{fn} {ln}".ljust(18), 10)
            _entry(c, L + 270, yy - 7, ssn, 10)
            _entry(c, L + 370, yy - 7, rel, 10)
        _check(c, R - 92, yy - 7, ctc)
        _check(c, R - 35, yy - 7, odc)
    y -= 56
    c.setLineWidth(1)
    c.line(L, y, R, y)

    # ---- income lines
    lines = [
        ("1a", "Total amount from Form(s) W-2, box 1 (see instructions)", "1a", "412,880."),
        ("b", "Household employee wages not reported on Form(s) W-2", "1b", ""),
        ("c", "Tip income not reported on line 1a (see instructions)", "1c", ""),
        ("d", "Medicaid waiver payments not reported on Form(s) W-2 (see instructions)", "1d", ""),
        ("e", "Taxable dependent care benefits from Form 2441, line 26", "1e", ""),
        ("f", "Employer-provided adoption benefits from Form 8839, line 29", "1f", ""),
        ("g", "Wages from Form 8919, line 6", "1g", ""),
        ("h", "Other earned income (see instructions)", "1h", ""),
        ("i", "Nontaxable combat pay election (see instructions)", "", ""),
        ("z", "Add lines 1a through 1h", "1z", "412,880."),
    ]
    _label(c, L, y - 10, "Income", 8, bold=True)
    for i, t in enumerate(["Attach Form(s)", "W-2 here. Also", "attach Forms", "W-2G and", "1099-R if tax", "was withheld."]):
        _label(c, L, y - 20 - i * 7, t, 5.8, bold=True)
    for i, t in enumerate(["If you did not", "get a Form", "W-2, see", "instructions."]):
        _label(c, L, y - 70 - i * 7, t, 5.8)
    ly = y - 10
    for num, text, box, val in lines:
        _label(c, L + 62, ly, num, 6.8, bold=True)
        _label(c, L + 72, ly, text, 6.6)
        if box:
            c.setLineWidth(0.4)
            c.rect(R - 112, ly - 3, 18, 10)
            _label(c, R - 110, ly, box, 6, bold=True)
            c.rect(R - 94, ly - 3, 94, 10)
        if val:
            _entry(c, R - 3, ly - 1, val, 9.5, right=True)
        ly -= 10.5
    pairs = [
        ("2a", "Tax-exempt interest", "2a", "6,214.", "b", "Taxable interest", "2b", "14,702."),
        ("3a", "Qualified dividends", "3a", "71,155.", "b", "Ordinary dividends", "3b", "88,409."),
        ("4a", "IRA distributions", "4a", "12,000.", "b", "Taxable amount", "4b", "12,000."),
        ("5a", "Pensions and annuities", "5a", "", "b", "Taxable amount", "5b", ""),
        ("6a", "Social security benefits", "6a", "", "b", "Taxable amount", "6b", ""),
    ]
    _label(c, L, ly - 2, "Attach Sch. B", 6.2)
    _label(c, L, ly - 9, "if required.", 6.2)
    for a, at, ab, av, b, bt, bb, bv in pairs:
        _label(c, L + 62, ly, a, 6.8, bold=True); _label(c, L + 74, ly, at, 6.6)
        c.rect(L + 195, ly - 3, 16, 10); _label(c, L + 197, ly, ab, 6, bold=True)
        c.rect(L + 211, ly - 3, 70, 10)
        if av:
            _entry(c, L + 279, ly - 1, av, 9.5, right=True)
        _label(c, L + 290, ly, b, 6.8, bold=True); _label(c, L + 300, ly, bt, 6.6)
        c.rect(R - 112, ly - 3, 18, 10); _label(c, R - 110, ly, bb, 6, bold=True); c.rect(R - 94, ly - 3, 94, 10)
        if bv:
            _entry(c, R - 3, ly - 1, bv, 9.5, right=True)
        ly -= 10.5
    rest = [
        ("c", "If you elect to use the lump-sum election method, check here (see instructions)", "", ""),
        ("7", "Capital gain or (loss). Attach Schedule D if required. If not required, check here", "7", "164,330."),
        ("8", "Additional income from Schedule 1, line 10", "8", "297,118."),
        ("9", "Add lines 1z, 2b, 3b, 4b, 5b, 6b, 7, and 8. This is your total income", "9", "989,439."),
        ("10", "Adjustments to income from Schedule 1, line 26", "10", "41,207."),
        ("11", "Subtract line 10 from line 9. This is your adjusted gross income", "11", "948,232."),
        ("12", "Standard deduction or itemized deductions (from Schedule A)", "12", "118,460."),
        ("13", "Qualified business income deduction from Form 8995 or Form 8995-A", "13", "11,902."),
        ("14", "Add lines 12 and 13", "14", "130,362."),
        ("15", "Subtract line 14 from line 11. If zero or less, enter -0-. This is your taxable income", "15", "817,870."),
    ]
    sd = ["Standard", "Deduction for -", "• Single or Married", "  filing separately,", "  $14,600",
          "• Married filing", "  jointly or", "  Qualifying", "  surviving spouse,", "  $29,200",
          "• Head of", "  household,", "  $21,900", "• If you checked", "  any box under",
          "  Standard", "  Deduction,", "  see instructions."]
    c.setLineWidth(0.4)
    c.rect(L, ly - 118, 58, 128)
    for i, t in enumerate(sd):
        _label(c, L + 2, ly + 2 - i * 6.6, t, 5.2, bold=i < 2)
    for num, text, box, val in rest:
        _label(c, L + 62, ly, num, 6.8, bold=True)
        _label(c, L + 74, ly, text, 6.6)
        if box:
            c.rect(R - 112, ly - 3, 18, 10); _label(c, R - 110, ly, box, 6, bold=True); c.rect(R - 94, ly - 3, 94, 10)
        if val:
            _entry(c, R - 3, ly - 1, val, 9.5, right=True)
        ly -= 12
    c.setLineWidth(1)
    c.line(L, ly + 2, R, ly + 2)
    _label(c, L, ly - 8, "For Disclosure, Privacy Act, and Paperwork Reduction Act Notice, see separate instructions.", 6.5, bold=True)
    _label(c, R - 60, ly - 8, "Form 1040 (2024)", 6.5)
    _label(c, L, ly - 18, "LHA   419421  12-30-24", 5.5)
    c.setFont("Helvetica", 9)
    c.drawCentredString(W / 2, ly - 32, "21")
    fiction_mark(c, W)
    c.save()
    return log
