"""Custodian / transfer-agent statements drawn directly on a canvas.

Layouts are generic approximations (no logos or trade dress), but the
information architecture mirrors real statements: consolidated summaries with
sub-accounts, registration lines, beneficiary blocks, boilerplate pages.
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import landscape, letter

from common import Col, LoggedCanvas, TextLog, barcode, fiction_mark, logo_box, paragraph, table, text_block
from facts import (EQUINITI_HOLDER, JPM_LP, JPM_TRUST_BRKG, JPM_TRUST_MAIN, JPM_TRUST_SUMMARY, LP, MS_ACCTS,
                   REBECCA, SCHWAB_JOINT, SCHWAB_ROTH, TRUST)

LAND = landscape(letter)


def mask_jpm(num: str) -> str:
    # 448-17731-0 -> XXX-X7731-0
    a, b, c = num.split("-")
    return f"XXX-X{b[1:]}-{c}"


# =========================================================================== J.P. Morgan style

JPM_TEAM = ["Your J.P. Morgan team:", "", "Alexandra Whitcombe, 704-555-0141", "Marcus Delacroix, 704-555-0158",
            "Priya Raman, 704-555-0177", "", "J.P. Morgan Securities LLC", "550 South Tryon Street", "Floor 29",
            "Charlotte, NC 28202", "", "Gregory Haines, Market Manager", "704-555-0100", "",
            "Please Direct Inquiries To: 704-555-0199"]

BOILER_CLASS_ACTION = (
    "The Class Action Claims Services Agreement is amended as of the Effective Date to provide that J.P. Morgan "
    "Securities LLC and/or a third-party service provider engaged by it may deposit a Recovery from a Covered "
    "Lawsuit into your Account in gross, followed by a debit to your Account for related Fees, or may continue to "
    "deposit a Recovery net of Fees. The agreement is further amended to authorize the return of unclaimed Recovery "
    "funds to the appropriate securities regulator if so required.")

BOILER_DEPOSIT = (
    "This is a bank deposit with JPMorgan Chase Bank, N.A., member FDIC, reflected here for your convenience; it is "
    "not cash held in your brokerage account. Securities and investments, other than deposit products, are not "
    "deposits or obligations of JPMorgan Chase Bank, N.A., are not FDIC insured, and are subject to investment "
    "risks, including possible loss of the principal amount invested.")

BOILER_TAX = (
    "Certain dividends shown here are characterized as \"qualified\" based on the prior tax classification of such "
    "dividends. The ultimate tax characterization cannot be determined until after the end of the taxable year. This "
    "statement should not be used for tax reporting and is not a substitute for IRS Form 1099. Please consult your "
    "tax advisor.")


class JPMStatement:
    W, H = LAND

    def __init__(self, path: Path, log: TextLog, *, total_pages: int, period: str, title_kind: str,
                 title_name: str, acct_footer: str):
        self.c = LoggedCanvas(str(path), log, pagesize=LAND)
        self.total = total_pages
        self.period = period
        self.title_kind = title_kind
        self.title_name = title_name
        self.acct_footer = acct_footer
        self.pageno = 0

    def header(self, section: str | None, name: str | None = None, period_line: str | None = None):
        c, W, H = self.c, self.W, self.H
        logo_box(c, 36, H - 70, 44, 40, ["J.P.", "Morgan"], size=9)
        c.setFont("Helvetica-Bold", 10)
        c.drawRightString(W - 36, H - 40, self.title_kind)
        c.setFont("Helvetica-Bold", 16)
        c.drawRightString(W - 36, H - 60, name or self.title_name)
        y = H - 78
        if section:
            c.setFont("Helvetica-Bold", 10)
            c.drawRightString(W - 36, y, section)
            y -= 13
        c.setFont("Helvetica", 8)
        c.drawRightString(W - 36, y, period_line or f"Period Ended {self.period.split(' to ')[1]}")
        c.setLineWidth(1.2)
        c.line(36, H - 100, W - 36, H - 100)

    def footer(self, acct=None):
        c = self.c
        c.setLineWidth(1.2)
        c.line(36, 40, self.W - 36, 40)
        c.setFont("Helvetica", 7)
        c.drawString(36, 30, f"Account No: {acct or self.acct_footer}")
        c.drawRightString(self.W - 36, 30, f"Page {self.pageno} of {self.total}")
        fiction_mark(c, self.W)

    def next(self, page_number: int):
        """Advance to a page with a given printed number (gaps simulate missing pages)."""
        if self.pageno:
            self.c.showPage()
        self.pageno = page_number

    def blank(self, page_number: int):
        self.next(page_number)
        c = self.c
        logo_box(c, 36, self.H - 70, 44, 40, ["J.P.", "Morgan"], size=9)
        c.setLineWidth(1.2)
        c.line(36, self.H - 100, self.W - 36, self.H - 100)
        c.setFont("Helvetica", 8)
        c.drawCentredString(self.W / 2, self.H / 2, "THIS PAGE INTENTIONALLY LEFT BLANK")
        c.line(36, 40, self.W - 36, 40)
        c.setFont("Helvetica", 7)
        c.drawRightString(self.W - 36, 30, f"Page {self.pageno} of {self.total}")
        fiction_mark(c, self.W)

    def cover(self, page_number, *, short_name, reg_lines, toc, mail_lines, acct, kind=None, name=None):
        self.next(page_number)
        c, W, H = self.c, self.W, self.H
        self.header(None, name, f"Period Covering {self.period}")
        if kind:
            c.setFont("Helvetica-Bold", 10)
            c.drawRightString(W - 36, H - 40, kind)
        y = H - 120
        y = text_block(c, 36, y, reg_lines, "Helvetica-Bold", 9.5, 12)
        text_block(c, 36, y - 10, JPM_TEAM, "Helvetica", 7.5, 10)
        # TOC
        tx = W - 300
        c.setFont("Helvetica", 7)
        c.drawRightString(W - 36, H - 118, "Page")
        ty = H - 130
        for label, pg, bold in toc:
            c.setFont("Helvetica-Bold" if bold else "Helvetica", 7.5)
            c.drawString(tx, ty, label)
            c.drawRightString(W - 40, ty, str(pg))
            c.setLineWidth(0.3)
            c.line(tx, ty - 3, W - 36, ty - 3)
            ty -= 12
        text_block(c, W / 2 + 40, 170, mail_lines, "Helvetica", 10, 12.5)
        self.footer(acct)

    def general_info(self, page_number, *, name, portfolio_number, individual=None, messages=True, acct=None):
        self.next(page_number)
        c, W, H = self.c, self.W, self.H
        self.header("General Information", name)
        y = H - 125
        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(36, y, "PORTFOLIO INFORMATION")
        c.setFont("Helvetica", 8)
        c.drawString(36, y - 16, "PORTFOLIO NUMBER :")
        c.drawString(200, y - 16, portfolio_number)
        c.drawString(36, y - 28, "BASE CURRENCY")
        c.drawString(200, y - 28, "US DOLLAR (USD)")
        y -= 52
        if individual:
            c.setFont("Helvetica-Bold", 8.5)
            c.drawString(36, y, "INDIVIDUAL PORTFOLIOS")
            y = table(c, 36, y - 14, [Col("PORTFOLIO NAME", 260), Col("PORTFOLIO NUMBER", 140), Col("PAGE", 50, "right")],
                      individual, size=8)
            y -= 10
        if messages:
            c.setFont("Helvetica-Bold", 8.5)
            c.drawString(36, y, "SPECIAL MESSAGES")
            c.setFont("Helvetica-Bold", 8)
            c.drawString(36, y - 14, "Important Changes to your Account Agreements")
            paragraph(c, 36, y - 27, BOILER_CLASS_ACTION, 430, size=7.8, leading=10)
        self.footer(acct)

    def overview(self, page_number, *, name, begin, interest, fees, change, end, cash, equity, acct=None,
                 zero=False):
        self.next(page_number)
        c, W, H = self.c, self.W, self.H
        self.header("Overview", name)
        y = H - 125
        c.setFont("Helvetica-Bold", 9)
        c.drawString(36, y, "TOTAL PORTFOLIO")
        if not zero:
            y = table(c, 36, y - 16, [Col("PORTFOLIO ASSET ALLOCATION (INCLUDES ACCRUALS)", 230),
                                      Col("Market Value", 90, "right"), Col("Percentage", 60, "right")],
                      [["CASH, DEPOSITS & MONEY MARKET FUNDS", cash, pct(cash, end)],
                       ["   DEPOSITS & MONEY MARKET FUNDS", cash, pct(cash, end)],
                       ["PUBLIC EQUITY", equity, pct(equity, end)],
                       ["   GLOBAL EQUITY", equity, pct(equity, end)],
                       ["TOTAL PORTFOLIO", end, "100.00"]], size=7.8, bold_rows={4})
            # donut stand-in
            c.setLineWidth(14)
            c.setStrokeGray(0.25)
            c.circle(W - 150, H - 190, 45)
            c.setStrokeGray(0)
            c.setLineWidth(1)
            c.setFont("Helvetica-Bold", 9)
            c.drawCentredString(W - 150, H - 193, end)
            y -= 10
        else:
            y -= 30
        rows = [["MARKET VALUE AS OF OCTOBER 01, 2025", ""], ["(INCLUDING ESTIMATED ACCRUALS)", begin]]
        if interest:
            rows.append(["INTEREST RECEIVED", interest])
        if fees:
            rows.append(["ACCOUNT FEES", fees])
        rows += [["CHANGE IN MARKET VALUE", change], ["MARKET VALUE AS OF OCTOBER 31, 2025", ""],
                 ["(INCLUDING ESTIMATED ACCRUALS)", end]]
        table(c, 36, y - 6, [Col("PORTFOLIO ACTIVITY", 230), Col("Market Value", 90, "right")], rows, size=7.8)
        table(c, 400, y - 6, [Col("INVESTMENT RESULTS\nCURRENT MONTH", 90), Col("Beginning\nMarket Value", 80, "right"),
                              Col("Net Deposits\n(Withdrawals)", 80, "right"), Col("Investment\nResults", 80, "right"),
                              Col("Ending\nMarket Value", 80, "right")],
              [["Oct 31 25", begin, "0.00", results(begin, end), end]], size=7.8)
        if not zero:
            paragraph(c, 36, 70, "This asset class may include bank deposits which are FDIC-insured and money market "
                      "funds which are not FDIC-insured, are subject to investment risk and may lose value.", 700,
                      size=6.5)
        self.footer(acct)

    def tax_summary(self, page_number, *, name, month, ytd, unrealized, acct=None):
        self.next(page_number)
        c, H = self.c, self.H
        self.header("US Tax Summary", name)
        y = table(c, 36, H - 130, [Col("REPORTABLE INCOME", 260), Col("Current Month", 90, "right"),
                                   Col("Quarter to Date", 90, "right"), Col("Year to Date", 90, "right")],
                  [["REPORTABLE INTEREST", "", "", ""], ["   Bank Interest", month, month, ytd],
                   ["TOTAL REPORTABLE INTEREST", month, month, ytd], ["TOTAL REPORTABLE INCOME", month, month, ytd]],
                  size=7.8, bold_rows={2, 3})
        table(c, 36, y - 16, [Col("UNREALIZED GAIN (LOSS)", 260), Col("", 90, "right")],
              [["CURRENT UNREALIZED GAIN (LOSS)", unrealized]], size=7.8)
        paragraph(c, 36, 80, BOILER_TAX, 700, size=6.5)
        self.footer(acct)

    def asset_strategy(self, page_number, *, name, cash, equity, end, fund, acct=None):
        self.next(page_number)
        c, H = self.c, self.H
        self.header("Asset Strategy Analysis", name)
        table(c, 36, H - 130, [Col("", 330), Col("Market Value\nas of Oct 31 25", 100, "right"),
                               Col("Percentage\nof Portfolio", 90, "right")],
              [["CASH, DEPOSITS & MONEY MARKET FUNDS", cash, pct(cash, end) + " %"],
               ["   DEPOSITS", cash, pct(cash, end) + " %"],
               ["PUBLIC EQUITY", equity, pct(equity, end) + " %"],
               ["   GLOBAL EQUITY", equity, pct(equity, end) + " %"], [f"      {fund}", equity, pct(equity, end) + " %"],
               ["TOTAL PORTFOLIO", end, "100.00 %"]], size=7.8, bold_rows={5})
        self.footer(acct)

    def holdings(self, page_number, *, name, cash, fund, ticker, qty, price, equity, unit_cost, cost, unreal,
                 est_income, end, acct=None):
        self.next(page_number)
        c, H = self.c, self.H
        self.header("Holdings", name)
        y = table(c, 36, H - 130,
                  [Col("CASH, DEPOSITS & MONEY MARKET FUNDS", 230), Col("Quantity", 70, "right"),
                   Col("Market\nPrice", 60, "right"), Col("Market Value/\nAccrued Income", 85, "right"),
                   Col("Unit Cost", 60, "right"), Col("Adjusted Cost/\nOriginal Cost", 85, "right"),
                   Col("Unrealized\nGain (Loss)", 70, "right"), Col("Estimated\nAnnual Income", 70, "right")],
                  [["DEPOSITS", "", "", "", "", "", "", ""],
                   ["JPMORGAN CHASE BANK DEPOSIT SWEEP", cash, "1.0000", cash, "1.0000", cash, "0.00", "31.07"]],
                  size=7.5)
        y = table(c, 36, y - 16,
                  [Col("PUBLIC EQUITY", 230), Col("Quantity", 70, "right"), Col("Market\nPrice", 60, "right"),
                   Col("Market Value/\nAccrued Income", 85, "right"), Col("Unit Cost", 60, "right"),
                   Col("Cost Basis", 85, "right"), Col("Unrealized\nGain (Loss)", 70, "right"),
                   Col("Estimated\nAnnual Income", 70, "right")],
                  [["GLOBAL EQUITY", "", "", "", "", "", "", ""],
                   [fund, qty, price, equity, unit_cost, cost, unreal, est_income], [f"({ticker})", "", "", "", "", "", "", ""]],
                  size=7.5)
        table(c, 36, y - 16, [Col("TOTAL PORTFOLIO", 300), Col("Market Value", 100, "right"),
                              Col("Unrealized Gain (Loss)", 120, "right")], [["", end, unreal]], size=7.8)
        paragraph(c, 36, 80, BOILER_DEPOSIT, 700, size=6.5)
        self.footer(acct)

    def cash_activity(self, page_number, *, name, acct_full, open_bal, fee, interest, close, acct=None):
        self.next(page_number)
        c, H = self.c, self.H
        self.header("Cash Activity", name)
        after_fee = money(num(open_bal) - num(fee.strip("()")))
        table(c, 36, H - 130,
              [Col("TRANSACTIONS AFFECTING CASH", 280), Col("Type of\nActivity", 80), Col("Settlement\nDate", 70),
               Col("Net Settlement\nAmount", 90, "right"), Col("End of Day\nBalance", 90, "right")],
              [["CLOSING BALANCE AS OF SEP 30 25", "", "", "", open_bal],
               [f"U S DOLLAR {acct_full} Qtr 3 Inv Mgmt Fee 30-Sep-25", "Fee", "Oct 29 25", fee, after_fee],
               ["Interest Earned on Bank Deposit Intended for Reinvestment", "Intr Recv", "Oct 31 25", interest, close],
               ["CLOSING BALANCE AS OF OCT 31 25", "", "", "", close]], size=7.6, bold_rows={3})
        self.footer(acct)

    def disclosures(self, page_number, acct=None):
        self.next(page_number)
        c, H = self.c, self.H
        self.header("Report Disclosures", None)
        y = H - 125
        for para in DISCLOSURES:
            y = paragraph(c, 36, y, para, 720, size=7, leading=9) - 6
        self.footer(acct)

    def save(self):
        self.c.save()


DISCLOSURES = [
    "This statement is provided by J.P. Morgan Securities LLC (\"JPMS\"), member FINRA and SIPC. Please review your "
    "statement carefully and promptly report any inaccuracy or discrepancy to your J.P. Morgan team and to JPMS "
    "Client Service. Any oral communications should be re-confirmed in writing to further protect your rights.",
    "Pricing: Securities are valued using prices obtained from sources believed to be reliable. Prices of thinly "
    "traded securities may be estimates. Values shown are not guaranteed and may differ from amounts realized on "
    "sale.",
    "Estimated annual income and yield are estimates only, may include return of principal or capital gains, and "
    "actual income may be lower or higher.",
    "SIPC: JPMS is a member of SIPC, which protects securities customers of its members up to $500,000 (including "
    "$250,000 for claims for cash). An explanatory brochure is available upon request or at www.sipc.org.",
    "Bank deposits held through the deposit sweep program are eligible for FDIC insurance up to applicable limits "
    "per depositor, per insured bank, for each account ownership category.",
    "Free credit balances are not segregated and may be used in the operation of JPMS's business, subject to the "
    "limitations of SEC Rule 15c3-3. You may demand payment of free credit balances at any time.",
    "Tax reporting: JPMS will report to the IRS on Forms 1099 as required. Cost basis information may be provided "
    "by you or a prior firm and may not have been verified.",
]


def num(s: str) -> float:
    return float(s.replace(",", "").replace("$", "").replace("(", "-").replace(")", ""))


def money(v: float) -> str:
    return f"{v:,.2f}"


def pct(part: str, whole: str) -> str:
    return f"{num(part) / num(whole) * 100:.2f}"


def results(begin, end):
    return money(num(end) - num(begin))


def build_jpm_trust(path: Path) -> TextLog:
    log = TextLog()
    S = JPMStatement(path, log, total_pages=20, period="October 01, 2025 to October 31, 2025",
                     title_kind="Investment Summary", title_name="BRADLEY DESCENDANTS IRREVOCABLE TRUST",
                     acct_footer=mask_jpm(JPM_TRUST_SUMMARY))
    mail = [REBECCA["full"].upper(), "410 Quail Hollow RD", "Charlotte NC 28226"]
    reg = ["BRADLEY DESCENDANTS IRREVOCABLE", f"TRUST U/A DTD {TRUST['custodian_dtd']} REBECCA L.", "BRADLEY, TRUSTEE"]
    v = dict(begin="1,163,207.44", interest="4.91", fees="(2.83)", change="23,232.65", end="1,186,442.17",
             cash="2,811.30", equity="1,183,630.87")
    S.cover(1, short_name="BRADLEY DESCENDANTS IRREVOCABLE TRUST", reg_lines=["BRADLEY DESCENDANTS IRREVOCABLE TRUST"],
            toc=[("BRADLEY DESCENDANTS IRREVOCABLE TRUST", 1, True), ("General Information", 2, False),
                 ("Overview", 3, False), ("US Tax Summary", 4, False), ("Asset Strategy Analysis", 5, False),
                 ("STATEMENT DETAIL", 7, True), ("Report Disclosures", 19, False)],
            mail_lines=mail, acct=mask_jpm(JPM_TRUST_SUMMARY))
    S.general_info(2, name="BRADLEY DESCENDANTS IRREVOCABLE TRUST", portfolio_number=JPM_TRUST_SUMMARY,
                   individual=[["BRADLEY DESCENDANTS IRREV TR BRKG", JPM_TRUST_BRKG, "7"],
                               ["BRADLEY DESCENDANTS IRREV TR", JPM_TRUST_MAIN, "11"]], messages=False)
    S.overview(3, name="BRADLEY DESCENDANTS IRREVOCABLE TRUST", **v)
    S.tax_summary(4, name="BRADLEY DESCENDANTS IRREVOCABLE TRUST", month="4.91", ytd="58.36", unrealized="497,215.40")
    S.asset_strategy(5, name="BRADLEY DESCENDANTS IRREVOCABLE TRUST", cash=v["cash"], equity=v["equity"], end=v["end"],
                     fund="JPM TAX AWARE GLOBAL EQUITY PORTFOLIO")
    S.blank(6)
    # --- sub-account 1: zero-balance brokerage
    b = mask_jpm(JPM_TRUST_BRKG)
    S.title_kind = "Statement Detail"
    S.cover(7, short_name="", reg_lines=reg,
            toc=[("BRADLEY DESCENDANTS IRREV TR BRKG", 7, True), ("General Information", 8, False),
                 ("Overview", 9, False), ("Report Disclosures", 19, False)],
            mail_lines=[], acct=b, kind="Statement Detail", name="BRADLEY DESCENDANTS IRREV TR BRKG")
    S.general_info(8, name="BRADLEY DESCENDANTS IRREV TR BRKG", portfolio_number=b, acct=b)
    S.overview(9, name="BRADLEY DESCENDANTS IRREV TR BRKG", begin="0.00", interest=None, fees=None, change="0.00",
               end="0.00", cash="0.00", equity="0.00", acct=b, zero=True)
    S.blank(10)
    # --- sub-account 2: the assets
    m = mask_jpm(JPM_TRUST_MAIN)
    S.cover(11, short_name="", reg_lines=reg,
            toc=[("BRADLEY DESCENDANTS IRREV TR", 11, True), ("General Information", 12, False),
                 ("Overview", 13, False), ("US Tax Summary", 14, False), ("Holdings", 15, False),
                 ("Cash Activity", 16, False), ("Bank Statement", 17, False), ("Report Disclosures", 19, False)],
            mail_lines=[], acct=m, kind="Statement Detail", name="BRADLEY DESCENDANTS IRREV TR")
    S.general_info(12, name="BRADLEY DESCENDANTS IRREV TR", portfolio_number=m, acct=m)
    S.overview(13, name="BRADLEY DESCENDANTS IRREV TR", acct=m, **v)
    S.tax_summary(14, name="BRADLEY DESCENDANTS IRREV TR", month="4.91", ytd="58.36", unrealized="497,215.40", acct=m)
    S.holdings(15, name="BRADLEY DESCENDANTS IRREV TR", cash="2,811.30", fund="JPM TAX AWARE GLOBAL EQUITY PORTFOLIO",
               ticker="JTAGX", qty="40,521.426", price="29.2100", equity="1,183,630.87", unit_cost="16.9395",
               cost="686,415.47", unreal="497,215.40", est_income="12,658.97", end="1,186,442.17", acct=m)
    S.cash_activity(16, name="BRADLEY DESCENDANTS IRREV TR", acct_full=m, open_bal="2,809.22", fee="(2.83)",
                    interest="4.91", close="2,811.30", acct=m)
    # pages 17-20 (bank statement, fees, disclosures) were not included in the scan
    S.save()
    return log


def build_jpm_lp(path: Path) -> TextLog:
    log = TextLog()
    a = mask_jpm(JPM_LP)
    S = JPMStatement(path, log, total_pages=8, period="October 01, 2025 to October 31, 2025",
                     title_kind="Statement Detail", title_name="BRADLEY CAPITAL PARTNERS", acct_footer=a)
    v = dict(begin="2,214,880.12", interest="19.47", fees="(11.26)", change="42,295.30", end="2,257,183.63",
             cash="11,186.52", equity="2,245,997.11")
    S.cover(1, short_name="", reg_lines=[LP["upper"]],
            toc=[("BRADLEY CAPITAL PARTNERS", 1, True), ("General Information", 2, False), ("Overview", 3, False),
                 ("US Tax Summary", 4, False), ("Holdings", 5, False), ("Cash Activity", 6, False),
                 ("Report Disclosures", 7, False)],
            mail_lines=[LP["upper"], *LP["address_upper"]], acct=a)
    S.general_info(2, name="BRADLEY CAPITAL PARTNERS", portfolio_number=JPM_LP)
    S.overview(3, name="BRADLEY CAPITAL PARTNERS", **v)
    S.tax_summary(4, name="BRADLEY CAPITAL PARTNERS", month="19.47", ytd="802.15", unrealized="1,176,402.88")
    S.holdings(5, name="BRADLEY CAPITAL PARTNERS", cash="11,186.52", fund="JPM TAX AWARE GLOBAL EQUITY PORTFOLIO",
               ticker="JTAGX", qty="76,891.375", price="29.2100", equity="2,245,997.11", unit_cost="13.9105",
               cost="1,069,594.23", unreal="1,176,402.88", est_income="24,021.04", end="2,257,183.63")
    S.cash_activity(6, name="BRADLEY CAPITAL PARTNERS", acct_full=a, open_bal="11,178.31", fee="(11.26)",
                    interest="19.47", close="11,186.52")
    S.disclosures(7)
    S.disclosures(8)
    S.save()
    return log


# =========================================================================== Schwab style

SCHWAB_UNDERSTANDING = [
    "Understanding Your Statement. Your statement reports the activity and positions in your account for the period "
    "shown. Please review it promptly and report any discrepancies to Schwab at 1-800-435-4000 within 10 days.",
    "Account Registration. The name(s) and title shown at the top of this statement reflect the registration on our "
    "records. Contact us if your registration or address is incorrect.",
    "Cost Basis. Cost basis is shown as provided by you, a prior custodian, or calculated by Schwab and is not "
    "verified for accounts transferred in. It is not a substitute for Form 1099-B.",
    "Bank Sweep. Uninvested cash is swept to deposit accounts at Charles Schwab Bank, SSB and affiliated banks, which "
    "are eligible for FDIC insurance up to applicable limits. Deposits are not protected by SIPC.",
    "Pricing. Market values are obtained from third-party pricing services and may not reflect the price at which a "
    "security could be sold. Securities that did not trade may be priced at the last bid.",
    "Standing Withholding Elections. For retirement accounts, distributions are subject to federal and, where "
    "applicable, state income tax withholding unless you elect otherwise. Your current elections are summarized on "
    "page 1.",
    "Investment Advisors. If you have authorized an independent investment advisor to manage your account, the "
    "advisor is not affiliated with Schwab, and Schwab does not supervise the advisor's activities.",
    "SIPC. Securities in your account are protected up to $500,000 by SIPC, including $250,000 for claims for cash. "
    "Explanatory brochure available at www.sipc.org.",
]


class SchwabStatement:
    W, H = letter

    def __init__(self, path: Path, log: TextLog, *, total, period, acct):
        self.c = LoggedCanvas(str(path), log)
        self.total, self.period, self.acct = total, period, acct
        self.pageno = 0

    def next(self):
        if self.pageno:
            self.footer()
            self.c.showPage()
        self.pageno += 1
        c, W, H = self.c, self.W, self.H
        c.setFont("Helvetica-Bold", 15)
        c.drawString(40, H - 56, "Charles Schwab & Co., Inc.")
        c.setFont("Helvetica", 10)
        c.drawRightString(W - 40, H - 46, self.period)
        c.setFont("Helvetica", 8)
        c.drawRightString(W - 40, H - 58, f"Account Number {self.acct}")
        c.setStrokeColorRGB(0.0, 0.33, 0.62)
        c.setLineWidth(1)
        c.line(40, H - 72, W - 40, H - 72)
        c.setStrokeGray(0)

    def footer(self, note=None):
        c = self.c
        c.setFont("Helvetica", 6.5)
        if note:
            c.drawCentredString(self.W / 2, 44, note)
        c.setFont("Helvetica", 8)
        c.drawRightString(self.W - 40, 30, f"Page {self.pageno} of {self.total}")
        fiction_mark(c, self.W)

    def save(self):
        self.footer()
        self.c.save()

    def front(self, *, reg_lines, title, begin, end, ytd_begin, ytd_change, change, deposits="$0.00",
              withdrawals="$0.00", income="$0.01", messages, perf_inception=None, advisor=True):
        self.next()
        c, W, H = self.c, self.W, self.H
        if advisor:
            text_block(c, W - 40, H - 92, ["HOLLIS & GRANT ADVISORY GROUP", "Independent Investment Advisor",
                                           "1515 Mockingbird Ln | Ste 210 | Charlotte, NC 28209",
                                           "704-555-0112 | service@hollisgrant.example"],
                       "Helvetica", 8, 10.5, right=True)
        c.setLineWidth(0.6)
        c.line(40, H - 145, W - 40, H - 145)
        barcode(c, 70, H - 172, self.acct)
        text_block(c, 70, H - 188, reg_lines, "Helvetica", 8.5, 10.5)
        text_block(c, W - 40, H - 182, ["Schwab Alliance Team", "800-515-2157", "Monday - Friday 8 a.m. to 8 p.m. ET",
                                        "", "Online Account Access", "schwaballiance.com"], "Helvetica", 8, 10.5,
                   right=True)
        y = H - 270
        c.setFillGray(0)
        c.rect(40, y - 4, W - 80, 18, stroke=0, fill=1)
        c.setFillGray(1)
        c.setFont("Helvetica-Bold", 10.5)
        c.drawString(46, y + 1, title)
        c.setFillGray(0)
        c.setFont("Helvetica", 7)
        c.drawString(46, y - 14, "Brokerage")
        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(46, y - 34, "Value This Statement")
        c.setFont("Helvetica-Bold", 17)
        c.drawString(46, y - 56, end)
        text_block(c, 46, y - 80, ["Last Statement     Prior Year-End", f"{begin}       {ytd_begin}"], "Helvetica", 7.5, 10)
        table(c, 250, y - 30, [Col("", 120), Col("This Statement", 85, "right"), Col("Year to Date", 85, "right")],
              [["Beginning Balance", begin, ytd_begin], ["   Deposits", deposits, deposits],
               ["   Income", income, income], ["   Withdrawals", withdrawals, withdrawals],
               ["   Expenses", "$0.00", "$0.00"], ["   Change in Value", change, ytd_change],
               ["Ending Balance", end, end]], size=7.5, rule=False, bold_rows={0, 6})
        if perf_inception:
            c.setFont("Helvetica", 6.5)
            c.drawString(46, y - 112, f"Performance Inception: {perf_inception}")
        y -= 140
        c.rect(40, y - 4, 160, 16, stroke=0, fill=1)
        c.setFillGray(1)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(46, y + 1, "Important Messages")
        c.setFillGray(0)
        y -= 20
        for m in messages:
            y = paragraph(c, 52, y, "• " + m, W - 110, size=7.5, leading=10) - 3

    def portfolio(self, *, messages_cont, cash_rows, positions, total, income_rows):
        self.next()
        c, W, H = self.c, self.W, self.H
        y = H - 92
        if messages_cont:
            c.setFont("Helvetica-Bold", 9)
            c.drawString(40, y, "Important Messages (continued)")
            y -= 14
            for m in messages_cont:
                y = paragraph(c, 40, y, m, W - 80, size=7.8, leading=10) - 2
            y -= 8
        c.setFont("Helvetica-Bold", 11)
        c.drawString(40, y, "Your Portfolio")
        y = table(c, 40, y - 14, [Col("Cash & Cash Alternatives", 260), Col("Quantity", 70, "right"),
                                  Col("Price", 60, "right"), Col("Value", 80, "right"), Col("Estimated\nIncome", 62, "right")],
                  cash_rows, size=7.5)
        y = table(c, 40, y - 8, [Col("Equities & Funds", 260), Col("Quantity", 70, "right"), Col("Price", 60, "right"),
                                 Col("Value", 80, "right"), Col("Unrealized\nGain/(Loss)", 62, "right")],
                  positions, size=7.5)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(40, y - 4, "Portfolio Total")
        c.drawRightString(510, y - 4, total)
        y -= 30
        c.setFont("Helvetica-Bold", 11)
        c.drawString(40, y, "Your Activity")
        table(c, 40, y - 14, [Col("Date", 60), Col("Activity Type", 90), Col("Description", 260),
                              Col("Amount", 80, "right")], income_rows, size=7.5)

    def boiler(self, title, paras):
        self.next()
        c, W, H = self.c, self.W, self.H
        c.setFont("Helvetica-Bold", 11)
        c.drawString(40, H - 95, title)
        y = H - 115
        for p in paras:
            y = paragraph(c, 40, y, p, W - 80, size=7.4, leading=9.6) - 7


def build_schwab_roth(path: Path) -> TextLog:
    log = TextLog()
    S = SchwabStatement(path, log, total=8, period="September 1 to September 30, 2025", acct=SCHWAB_ROTH)
    S.front(reg_lines=["ROBERT W BRADLEY II", "CHARLES SCHWAB & CO INC CUST", "ROTH CONTRIBUTORY IRA",
                       "4410 QUAIL HOLLOW RD", "CHARLOTTE NC 28210"],
            title=f"Bradley II, Robert - Roth IRA Account Summary - #{SCHWAB_ROTH}",
            begin="$187,402.55", end="$191,118.04", ytd_begin="$171,950.12", change="$3,715.49",
            ytd_change="$19,167.92", income="$0.00",
            messages=["Your account purpose is Growth, with a moderately aggressive risk tolerance and a 15 to 20 "
                      "year time horizon.",
                      "Your Distribution Standing Withholding Elections: Federal Withholding Election (No Election "
                      "on File); State (SC) Withholding Election (State Withholding not available). Please see "
                      "Standing Withholding Elections on the Understanding Your Statement page.",
                      "Charles Schwab & Co., Inc., Custodian | Member SIPC"],
            perf_inception="03/18/2011")
    S.portfolio(
        messages_cont=["Primary Beneficiaries: Catherine M Bradley (100.00%)",
                       "Contingent Beneficiaries: Henry R Bradley (33.34%), Olivia C Bradley (33.33%), "
                       "Samuel T Bradley (33.33%)"],
        cash_rows=[["Schwab Bank Sweep - 0.45%", "", "", "$1,202.44", "$5.41"]],
        positions=[["VANGUARD TOTAL STOCK MARKET ETF (VTI)", "410.000", "$318.44", "$130,560.40", "$61,204.33"],
                   ["ISHARES CORE MSCI EAFE ETF (IEFA)", "520.000", "$84.12", "$43,742.40", "$9,018.77"],
                   ["SCHWAB US DIVIDEND EQUITY ETF (SCHD)", "560.000", "$27.88", "$15,612.80", "$1,402.15"]],
        total="$191,118.04",
        income_rows=[["09/30/2025", "Interest", "Schwab Bank Sweep Interest", "$0.00"]])
    S.boiler("Understanding Your Statement", SCHWAB_UNDERSTANDING[:4])
    S.boiler("Understanding Your Statement (continued)", SCHWAB_UNDERSTANDING[4:])
    S.boiler("Understanding Your Statement (continued)", SCHWAB_UNDERSTANDING[2:6])
    S.boiler("Retirement Account Information",
             ["Roth IRA contributions for 2025 may be made until April 15, 2026. Qualified distributions are generally "
              "tax-free if the account has been open five years and you are age 59 1/2 or older.",
              "Beneficiary designations on file with Schwab govern the distribution of this account at death and "
              "override any will or trust. Review your designations periodically."])
    S.boiler("Important Account Information", SCHWAB_UNDERSTANDING[6:])
    S.boiler("", [])
    S.save()
    return log


def build_schwab_joint(path: Path) -> TextLog:
    log = TextLog()
    S = SchwabStatement(path, log, total=6, period="October 1 to October 31, 2025", acct=SCHWAB_JOINT)
    S.front(reg_lines=["ROBERT W BRADLEY & CATHERINE M BRADLEY", "JT TEN 4410 QUAIL HOLLOW", "RD CHARLOTTE 28210"],
            title=f"BRADLEY II, ROBERT W & BRADLEY, CATHERINE M - JTWROS Account Summary - #{SCHWAB_JOINT}",
            begin="$842,113.07", end="$851,960.44", ytd_begin="$905,287.18", change="$9,812.15",
            ytd_change="$41,870.09", income="$35.22", withdrawals="$0.00",
            messages=["Your account purpose is Wealth Accumulation & Provide Income, with a moderate risk "
                      "tolerance and a time horizon less than 5 years.",
                      "Account carried by Charles Schwab & Co., Inc. Member SIPC."])
    S.portfolio(
        messages_cont=[],
        cash_rows=[["Schwab Bank Sweep - 0.45%", "", "", "$6,402.91", "$28.81"],
                   ["SCHWAB VALUE ADVANTAGE MONEY FUND (SWVXX)", "21,880.410", "$1.000", "$21,880.41", "$919.98"]],
        positions=[["DODGE & COX STOCK FUND CL I (DODGX)", "1,402.118", "$271.06", "$380,058.11", "$141,226.70"],
                   ["VANGUARD WELLINGTON FD ADMIRAL (VWENX)", "5,207.407", "$85.19", "$443,619.01", "$95,775.44"]],
        total="$851,960.44",
        income_rows=[["10/01/2025", "Dividend", "SCHWAB VALUE ADVANTAGE MONEY FUND", "$32.60"],
                     ["10/01/2025", "Reinvest", "SCHWAB VALUE ADVANTAGE MONEY FUND 1.000", "$(32.60)"],
                     ["10/31/2025", "Interest", "Schwab Bank Sweep Interest", "$2.62"]])
    S.boiler("Understanding Your Statement", SCHWAB_UNDERSTANDING[:4])
    S.boiler("Understanding Your Statement (continued)", SCHWAB_UNDERSTANDING[4:])
    S.boiler("Understanding Your Statement (continued)", SCHWAB_UNDERSTANDING[1:4])
    S.boiler("Important Account Information", SCHWAB_UNDERSTANDING[6:])
    S.save()
    return log


# =========================================================================== Morgan Stanley style

class MSStatement:
    W, H = LAND

    def __init__(self, path, log):
        self.c = LoggedCanvas(str(path), log, pagesize=LAND)
        self.started = False

    def page(self, local_no, local_total, *, kind="Consolidated Summary"):
        if self.started:
            self.c.showPage()
        self.started = True
        c, W, H = self.c, self.W, self.H
        c.setFont("Times-Bold", 16)
        c.drawString(36, H - 50, "Morgan Stanley")
        c.setFont("Helvetica", 7.5)
        text_block(c, 160, H - 36, ["Morgan Stanley Smith Barney LLC", "Wealth Management",
                                    "6000 Fairview Road, Suite 1100", "Charlotte, NC 28210-2252"], "Helvetica", 7, 8.5)
        c.setFont("Times-Roman", 18)
        c.drawCentredString(W / 2 + 60, H - 46, kind.upper())
        c.setFont("Helvetica", 10)
        c.drawCentredString(W / 2 + 60, H - 60, "October 1 - 31, 2025")
        c.setFont("Helvetica-Bold", 8)
        c.drawString(36, 30, "Member SIPC")
        c.drawRightString(W - 36, 30, f"Page {local_no} of {local_total}")
        fiction_mark(c, W)

    def reg(self, x, y, lines):
        return text_block(self.c, x, y, lines, "Helvetica", 8.5, 10.5)

    def save(self):
        self.c.save()


REG_MS = ["Robert W Bradley Il", "Catherine M Bradley", "JTWROS", "4410 Quail Hollow Rd.", "Charlotte, NC. 28210"]


def build_morgan_stanley(path: Path) -> TextLog:
    log = TextLog()
    S = MSStatement(path, log)
    c, W, H = S.c, S.W, S.H
    a1, a2, a3 = MS_ACCTS
    # --- consolidated summary, 6 pages
    S.page(1, 6)
    c.setFont("Helvetica", 6.5)
    c.drawString(160, H - 82, "CMS6631018814 1025 2R 0")
    S.reg(W / 2 + 20, H - 120, REG_MS)
    S.page(2, 6)  # intentionally blank reverse side
    S.page(3, 6)
    c.setFont("Helvetica", 6.5)
    c.drawString(160, H - 82, "CMS6631018816 1025 2R 0")
    S.reg(W / 2 + 20, H - 95, REG_MS)
    text_block(c, 36, H - 160, ["Your Financial Advisor:", "THE CATAWBA RIVER GROUP", "Branch: 704-555-0300/800-555-0412",
                                "", "Visit our website:", "www.morganstanley.com/wealth"], "Helvetica", 8, 10)
    c.setFont("Times-Roman", 15)
    c.drawString(300, H - 170, "Value of your portfolio")
    table(c, 300, H - 190, [Col("", 170), Col("on September 30 ($)", 110, "right"), Col("on October 31 ($)", 110, "right")],
          [["Your assets", "2,618,904.33", "2,655,117.80"], ["Your liabilities", "0.00", "0.00"],
           ["Value of your portfolio", "$2,618,904.33", "$2,655,117.80"]], size=8, bold_rows={2})
    text_block(c, W - 220, H - 290, ["Sources of your portfolio growth during 2025",
                                     "Value of your portfolio at year end 2024   $2,470,662.15",
                                     "Net deposits and withdrawals   -$96,000.00",
                                     "Dividend and interest income   $61,309.47",
                                     "Change in market value   $219,146.18",
                                     "Value of your portfolio on Oct 31, 2025   $2,655,117.80"], "Helvetica", 7, 10)
    S.page(4, 6)
    S.reg(W / 2 + 20, H - 95, ["Your Financial Advisor:", "THE CATAWBA RIVER GROUP"])
    c.setFont("Times-Roman", 15)
    c.drawString(36, H - 140, "Your portfolio balance sheet")
    table(c, 36, H - 160, [Col("Summary of your assets", 200), Col("Value on\nOctober 31 ($)", 100, "right"),
                           Col("Percentage of\nyour portfolio", 90, "right")],
          [["A Cash and money balances", "18,204.66", "0.69%"], ["B Cash alternatives", "0.00", "0.00%"],
           ["C Equities", "1,744,019.31", "65.69%"], ["D Fixed income", "612,880.14", "23.08%"],
           ["E Non-traditional", "280,013.69", "10.55%"], ["Total assets", "2,655,117.80", "100.00%"]],
          size=8, bold_rows={5})
    S.page(5, 6)
    c.setFont("Times-Roman", 15)
    c.drawString(36, H - 100, "Accounts in your portfolio")
    table(c, 36, H - 120, [Col("Account number", 110), Col("Account name and type", 260),
                           Col("Value on\nSeptember 30($)", 110, "right"), Col("Value on\nOctober 31 ($)", 110, "right"),
                           Col("Percentage\nof portfolio", 80, "right")],
          [[a1[0], f"{a1[1]} - {a1[2]}", "642,118.20", "651,402.77", "24.53%"],
           [a2[0], f"{a2[1]} - {a2[2]}", "1,702,390.44", "1,723,701.34", "64.92%"],
           [a3[0], f"{a3[1]} - {a3[2]}", "274,395.69", "280,013.69", "10.55%"],
           ["", "Total", "$2,618,904.33", "$2,655,117.80", "100 %"]], size=8, bold_rows={3})
    c.setFont("Times-Roman", 13)
    c.drawString(36, H - 245, "Change in the value of your accounts")
    # NOTE: account number typo (104474 vs 104477) is intentional; real statements have these.
    table(c, 36, H - 262, [Col("Account", 150), Col("Opening value\non October 1 ($)", 100, "right"),
                           Col("Deposits ($)", 80, "right"), Col("Withdrawals\nand fees ($)", 90, "right"),
                           Col("Dividend and\ninterest income ($)", 100, "right"),
                           Col("Change in\nmarket value ($)", 100, "right"), Col("Closing value\non October 31 ($)", 110, "right")],
          [["228-104474-118 Active Assets", "642,118.20", "0.00", "-1,240.00", "2,214.36", "8,310.21", "651,402.77"],
           [f"{a2[0]} Select UMA", "1,702,390.44", "0.00", "-4,402.18", "6,190.11", "19,522.97", "1,723,701.34"],
           [f"{a3[0]} Alternatives", "274,395.69", "0.00", "0.00", "3,110.00", "2,508.00", "280,013.69"]], size=7.6)
    S.page(6, 6)
    c.setFont("Times-Roman", 13)
    c.drawString(36, H - 100, "Dividend and interest income earned by account")
    paragraph(c, 36, H - 118, "For purposes of this statement, taxability of interest and dividend income has been "
              "determined from a US tax reporting perspective. The client monthly statement is not intended to be used "
              "and cannot be relied upon for tax purposes. Clients should refer to the Forms 1099 they receive "
              "annually.", 700, size=7.2, leading=9)
    table(c, 36, H - 160, [Col("Taxable accounts", 220), Col("Taxable dividends ($)", 110, "right"),
                           Col("Taxable interest ($)", 110, "right"), Col("Year to date ($)", 110, "right")],
          [[f"{a1[0]} {a1[1]}", "2,190.04", "24.32", "22,018.40"], [f"{a2[0]} Select UMA", "6,180.77", "9.34", "31,177.07"],
           [f"{a3[0]} Alternatives", "3,110.00", "0.00", "8,114.00"], ["Total taxable accounts", "$11,480.81", "$33.66", "$61,309.47"]],
          size=7.8, bold_rows={3})
    # --- account statement: Active Assets (6 pages)
    for i in range(1, 7):
        S.page(i, 6, kind="Active Assets Account")
        if i == 1:
            c.setFont("Helvetica", 6.5)
            c.drawString(160, H - 82, "CMS6631018822 1025 2R 0")
            text_block(c, 36, H - 120, ["Account name: Robert W Bradley Il", "                      Catherine M Bradley",
                                        "                      JTWROS", f"Account number: {a1[0]}"],
                       "Helvetica-Bold", 8.5, 11)
            S.reg(W / 2 + 20, H - 95, REG_MS)
            text_block(c, 36, H - 185, ["Your Financial Advisor:", "THE CATAWBA RIVER GROUP",
                                        "Questions about your statement?", "Call your Financial Advisor or Client Service",
                                        "at 800-869-3326."], "Helvetica", 8, 10)
            c.setFont("Times-Roman", 15)
            c.drawString(300, H - 200, "Value of your account")
            table(c, 300, H - 220, [Col("", 170), Col("on September 30 ($)", 110, "right"), Col("on October 31 ($)", 110, "right")],
                  [["Your assets", "642,118.20", "651,402.77"], ["Your liabilities", "0.00", "0.00"],
                   ["Value of your account", "$642,118.20", "$651,402.77"]], size=8, bold_rows={2})
        elif i == 2:
            text_block(c, 36, H - 95, ["Account name:  Robert W Bradley Il", f"Account number:  {a1[0]}"], "Helvetica", 8, 10)
            table(c, 36, H - 130, [Col("Holdings", 260), Col("Quantity", 80, "right"), Col("Price ($)", 70, "right"),
                                   Col("Value ($)", 100, "right"), Col("Unrealized\ngain/loss ($)", 100, "right")],
                  [["MICROSOFT CORP (MSFT)", "310.000", "517.81", "160,521.10", "88,214.06"],
                   ["JPMORGAN CHASE & CO (JPM)", "520.000", "309.02", "160,690.40", "71,902.11"],
                   ["COSTCO WHOLESALE CORP (COST)", "120.000", "912.40", "109,488.00", "40,015.30"],
                   ["ALPHABET INC CL A (GOOGL)", "640.000", "281.19", "179,961.60", "102,447.89"],
                   ["MS BANK DEPOSIT PROGRAM", "", "", "18,204.66", ""],
                   ["Total", "", "", "651,402.77", ""]], size=7.8, bold_rows={5})
        elif i == 3:
            text_block(c, 36, H - 95, ["Account activity this month"], "Times-Roman", 13)
            table(c, 36, H - 120, [Col("Date", 60), Col("Activity", 90), Col("Description", 360), Col("Amount ($)", 100, "right")],
                  [["Oct 2", "Dividend", "COSTCO WHOLESALE CORP PAID ON 120 SHS", "156.00"],
                   ["Oct 9", "Dividend", "JPMORGAN CHASE & CO PAID ON 520 SHS", "728.00"],
                   ["Oct 15", "Fee", "ACCOUNT FEE", "-1,240.00"],
                   ["Oct 31", "Interest", "MS BANK DEPOSIT PROGRAM", "24.32"]], size=7.8)
        else:
            S.reg(36, H - 95, ["Important information about your statement"])
            y = H - 120
            for para in SCHWAB_UNDERSTANDING[(i - 4) * 2:(i - 4) * 2 + 3]:
                y = paragraph(c, 36, y, para.replace("Schwab", "Morgan Stanley").replace("Charles Schwab Bank, SSB",
                                                                                          "Morgan Stanley Bank, N.A."),
                              720, size=7.2, leading=9.2) - 6
    # --- account statement: Select UMA (4 pages)
    for i in range(1, 5):
        S.page(i, 4, kind="Select UMA")
        if i == 1:
            text_block(c, 36, H - 120, ["Account name: Robert W Bradley Il", "                      Catherine M Bradley JTWROS",
                                        "Friendly account name: Family Core UMA", f"Account number: {a2[0]}"],
                       "Helvetica-Bold", 8.5, 11)
            S.reg(W / 2 + 20, H - 95, REG_MS)
            table(c, 300, H - 220, [Col("", 170), Col("on September 30 ($)", 110, "right"), Col("on October 31 ($)", 110, "right")],
                  [["Your assets", "1,702,390.44", "1,723,701.34"], ["Value of your account", "$1,702,390.44", "$1,723,701.34"]],
                  size=8, bold_rows={1})
        elif i == 2:
            table(c, 36, H - 120, [Col("Investment manager / sleeve", 300), Col("Value ($)", 110, "right"), Col("%", 60, "right")],
                  [["Eaton Vance Tax-Managed Core - Large Cap", "861,850.67", "50.0%"],
                   ["Nuveen Municipal Ladder 1-10 Yr", "612,880.14", "35.6%"], ["Cash", "4,210.03", "0.2%"],
                   ["International ADR - Lazard", "244,760.50", "14.2%"]], size=7.8)
        else:
            y = H - 110
            for para in SCHWAB_UNDERSTANDING[3:6]:
                y = paragraph(c, 36, y, para.replace("Schwab", "Morgan Stanley"), 720, size=7.2, leading=9.2) - 6
    S.save()
    return log


# =========================================================================== transfer agent (DRIP)

def build_equiniti(path: Path) -> TextLog:
    log = TextLog()
    c = LoggedCanvas(str(path), log)
    W, H = letter
    acct = f"C{EQUINITI_HOLDER}"
    c.setFont("Helvetica-Bold", 20)
    c.drawString(40, H - 60, "Carolina Power & Gas")
    c.setFont("Helvetica", 7.5)
    c.drawRightString(W - 40, H - 30, "Page 1 of 4")
    c.setFont("Helvetica-Bold", 13)
    c.drawRightString(W - 40, H - 52, "equiniti")
    text_block(c, W - 40, H - 66, ["Equiniti Trust Company, LLC", "PO Box 64874", "St. Paul, MN 55164-0874",
                                   "Within USA: 800 555 0187", "Outside USA: 651 555 0190",
                                   "Carolina Power & Gas Corporation is incorporated", "under the laws of the State of North Carolina."],
               "Helvetica", 7, 9, right=True)
    barcode(c, 60, H - 125, acct, w=170)
    c.setFont("Helvetica", 7)
    c.drawString(250, H - 120, "0E-3391")
    text_block(c, 60, H - 150, ["ROBERT W BRADLEY II", "4410 QUAIL HOLLOW RD", "CHARLOTTE NC 28210"],
               "Times-Roman", 10, 12)
    text_block(c, 330, H - 160, ["Holder Account Number"], "Helvetica-Bold", 9)
    text_block(c, 330, H - 173, [acct], "Helvetica", 10)
    barcode(c, 330, H - 200, acct + "x", w=160, h=14)
    text_block(c, 330, H - 215, ["Ticker Symbol   CPGX", "CUSIP   14388Q105"], "Helvetica", 7.5, 9)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(W / 2, H - 250, "PLEASE READ THE IMPORTANT PRIVACY NOTICE AT BACK OF STATEMENT")
    c.setFillGray(0.85)
    c.rect(40, H - 275, W - 80, 16, stroke=0, fill=1)
    c.setFillGray(0)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(46, H - 270, "Carolina Power & Gas Corporation - Investor Direct Choice Plan Statement")
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(40, H - 295, "Summary of Account Holdings as of 15 Sep 2025")
    table(c, 40, H - 310, [Col("Type of Holding", 140), Col("Opening\nBalance as of\n01 Jan 2025", 80, "right"),
                           Col("Share/Unit\nActivity", 70, "right"), Col("Closing\nBalance as of\n15 Sep 2025", 80, "right"),
                           Col("Price per\nShare/Unit\n(USD)", 70, "right"), Col("Closing Value as of\n15 Sep 2025\n(USD)", 92, "right")],
          [["DSPP - Common Stock", "612.408113", "19.777091", "632.185204", "94.17", "59,532.88"]], size=7.2)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(40, H - 400, "Dividend Reinvestment Activity")
    table(c, 40, H - 415, [Col("Record\nDate", 55), Col("Payment\nDate", 55), Col("Dividend\nRate\n(USD)", 55, "right"),
                           Col("Class\nDescription", 60), Col("Shares/Units\nReinvested", 70, "right"),
                           Col("Gross\nDividend\n(USD)", 65, "right"), Col("Taxes\nWithheld\n(USD)", 55, "right"),
                           Col("Net\nDividend\nReinvested", 60, "right")],
          [["15 Aug 2025", "15 Sep 2025", "1.045000", "Common", "6.836215", "655.07", "", "655.07"]], size=7)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(40, H - 500, "Year-to-Date Investment Plan Summary")
    table(c, 40, H - 515, [Col("Type of Activity", 150), Col("Gross Amount\n(USD)", 90, "right"),
                           Col("Taxes/Fees/Other\n(USD)", 90, "right"), Col("Net Amount\n(USD)", 90, "right"),
                           Col("Shares/Units", 90, "right")],
          [["DSPP - Common Stock Dividends", "1,926.33", "0.00", "1,926.33", "19.777091"]], size=7.2)
    c.setFont("Helvetica", 6.5)
    c.drawString(40, 40, "0E3391_EN_01 (Rev 0825)")
    fiction_mark(c, W)
    c.showPage()

    # page 2
    c.setFont("Helvetica-Bold", 8)
    text_block(c, 40, H - 40, ["Company Name", "Carolina Power & Gas Corporation"], "Helvetica-Bold", 8, 10)
    text_block(c, 230, H - 40, ["Statement Period", "01 Jan 2025 - 15 Sep 2025"], "Helvetica-Bold", 8, 10)
    text_block(c, 400, H - 40, ["Holder Account Number", acct], "Helvetica-Bold", 8, 10)
    c.setFont("Helvetica", 8)
    c.drawRightString(W - 40, H - 70, "Page 2 of 4")
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, H - 100, "Transaction Activity")
    table(c, 40, H - 118, [Col("Transaction\nDate", 60), Col("Transaction Description", 110), Col("Gross\nAmount\n(USD)", 55, "right"),
                           Col("Taxes\nWithheld\n(USD)", 50, "right"), Col("Net Amount\n(USD)", 60, "right"),
                           Col("Price per\nShare/Unit\n(USD)", 60, "right"), Col("Transaction\nShares/Units", 65, "right"),
                           Col("Total\nShares/Units", 70, "right")],
          [["DSPP - Common Stock", "", "", "", "", "", "", ""], ["", "Balance Forward", "", "", "", "", "", "612.408113"],
           ["17 Mar 2025", "Dividend Reinvestment", "639.98", "", "639.98", "97.881020", "6.538379", "618.946492"],
           ["16 Jun 2025", "Dividend Reinvestment", "631.28", "", "631.28", "98.217004", "6.402497", "625.348989"],
           ["15 Sep 2025", "Dividend Reinvestment", "655.07", "", "655.07", "95.822411", "6.836215", "632.185204"]],
          size=7)
    c.setFont("Helvetica", 6.5)
    c.drawString(40, 40, "0E3391")
    fiction_mark(c, W)
    c.showPage()

    # page 3: privacy notice (page 4 missing from the upload)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, H - 60, "PRIVACY NOTICE")
    y = H - 80
    for para in ["Equiniti Trust Company, LLC respects your privacy. We collect nonpublic personal information about "
                 "you from forms you submit and from your transactions with us, such as your name, address, social "
                 "security number and account balances.",
                 "We do not disclose nonpublic personal information about current or former shareholders to anyone, "
                 "except as permitted by law, including to service providers that help us administer your account.",
                 "We restrict access to your information to employees and agents who need it to service your account, "
                 "and we maintain physical, electronic and procedural safeguards to protect it."]:
        y = paragraph(c, 40, y, para, W - 80, size=8, leading=10.5) - 8
    c.setFont("Helvetica", 8)
    c.drawRightString(W - 40, 40, "Page 3 of 4")
    fiction_mark(c, W)
    c.save()
    return log
