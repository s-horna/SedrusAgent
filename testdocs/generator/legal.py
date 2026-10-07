"""Born-digital legal instruments (reportlab platypus), like a law-firm Word export."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

from common import TextLog
from facts import CATHERINE, DANIEL, HENRY, OLIVIA, REBECCA, ROBERT, SAMUEL, TRUST

SPECIMEN = ("SPECIMEN - SAMPLE DOCUMENT PREPARED FOR SOFTWARE TESTING PURPOSES ONLY. "
            "NOT A LEGAL INSTRUMENT. ALL PERSONS AND ENTITIES ARE FICTITIOUS.")

BASE = ParagraphStyle("base", fontName="Times-Roman", fontSize=11, leading=16.5, alignment=TA_JUSTIFY,
                      firstLineIndent=0.4 * inch, spaceAfter=6)
NOINDENT = ParagraphStyle("noindent", parent=BASE, firstLineIndent=0)
TITLE = ParagraphStyle("title", parent=BASE, fontName="Times-Bold", fontSize=15, alignment=TA_CENTER,
                       firstLineIndent=0, spaceAfter=10, leading=20)
SUBTITLE = ParagraphStyle("subtitle", parent=TITLE, fontName="Times-Roman", fontSize=11.5, leading=16)
ARTICLE = ParagraphStyle("article", parent=TITLE, fontSize=11, spaceBefore=10, spaceAfter=2, leading=15)
SECTION = ParagraphStyle("section", parent=NOINDENT, fontName="Times-Bold", spaceBefore=4, spaceAfter=3)
ITEM = ParagraphStyle("item", parent=BASE, firstLineIndent=0, leftIndent=0.75 * inch)
SIG = ParagraphStyle("sig", parent=NOINDENT, spaceAfter=2, alignment=0)
CENTER = ParagraphStyle("center", parent=NOINDENT, alignment=TA_CENTER)


class LoggedDoc(SimpleDocTemplate):
    def __init__(self, path, log: TextLog, footer_left: str, **kw):
        super().__init__(str(path), pagesize=letter, leftMargin=1.05 * inch, rightMargin=1.05 * inch,
                         topMargin=1.0 * inch, bottomMargin=1.0 * inch, title="", author="",
                         creator="", producer="", **kw)
        self.log = log
        self.footer_left = footer_left

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):
            self.log.add(self.page, flowable.getPlainText())
        elif isinstance(flowable, Table):
            for row in flowable._cellvalues:
                for cell in row:
                    items = cell if isinstance(cell, (list, tuple)) else [cell]
                    for it in items:
                        self.log.add(self.page, it.getPlainText() if isinstance(it, Paragraph) else str(it))

    def handle_pageBegin(self):
        super().handle_pageBegin()

    def footer(self, canv, doc):
        canv.saveState()
        canv.setFont("Times-Roman", 8)
        canv.drawString(self.leftMargin, 0.6 * inch, self.footer_left)
        canv.drawRightString(letter[0] - self.rightMargin, 0.6 * inch, f"Page {doc.page}")
        self.log.add(doc.page, f"{self.footer_left} Page {doc.page}")
        canv.setFont("Times-Italic", 6.5)
        canv.setFillColor(colors.HexColor("#9a9a9a"))
        canv.drawCentredString(letter[0] / 2, 0.42 * inch, SPECIMEN)
        canv.restoreState()

    def go(self, story):
        self.build(story, onFirstPage=self.footer, onLaterPages=self.footer)


def P(text, style=BASE):
    return Paragraph(text, style)


def kv_table(rows, col1=1.55 * inch, col2=4.6 * inch):
    data = [[Paragraph(f"<b>{k}</b>", NOINDENT), Paragraph(v, NOINDENT)] for k, v in rows]
    t = Table(data, colWidths=[col1, col2])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 1), ("TOPPADDING", (0, 0), (-1, -1), 1)]))
    return t


def sig_block(label, name, extra=None):
    lines = [Spacer(1, 18), P(f"<b>{label}</b>", SIG) if label else Spacer(1, 1), Spacer(1, 16),
             P("_________________________________________", SIG), P(name, SIG)]
    if extra:
        lines.append(P(extra, SIG))
    return KeepTogether(lines)


# =========================================================================== trust

def build_trust_agreement(path: Path) -> TextLog:
    log = TextLog()
    doc = LoggedDoc(path, log, "BRADLEY DESCENDANTS IRREVOCABLE TRUST AGREEMENT")
    R, C = ROBERT["full"].upper(), CATHERINE["full"].upper()
    RB, DW = REBECCA["full"].upper(), DANIEL["full"].upper()
    s = []

    # ---- cover
    s += [Spacer(1, 1.1 * inch), P("IRREVOCABLE TRUST AGREEMENT", TITLE),
          P("THE BRADLEY DESCENDANTS IRREVOCABLE TRUST", SUBTITLE), Spacer(1, 0.35 * inch),
          P(f"Dated {TRUST['date_long']}", SUBTITLE), Spacer(1, 0.5 * inch),
          kv_table([
              ("Grantors:", f"{ROBERT['full']} and {CATHERINE['full']}"),
              ("", "4410 Quail Hollow Road, Charlotte, North Carolina 28210"),
              ("Trustee:", REBECCA["full"]),
              ("", "410 Quail Hollow Road, Charlotte, North Carolina 28226"),
              ("Beneficiaries:", f"{HENRY['full']}, {OLIVIA['full']}, {SAMUEL['full']}"),
              ("Trust EIN:", TRUST["ein"]),
              ("Governing Law:", "State of North Carolina"),
              ("Type of Trust:", "Irrevocable; non-grantor for federal income tax purposes"),
          ]),
          Spacer(1, 0.9 * inch), P("Prepared by:", CENTER), P("PEMBERTON &amp; VANCE LLP", CENTER),
          P("Counselors at Law", CENTER), P("301 South College Street, Suite 3900, Charlotte, North Carolina 28202", CENTER),
          PageBreak()]

    # ---- preamble and recitals
    s += [P("IRREVOCABLE TRUST AGREEMENT", TITLE),
          P(f"THIS IRREVOCABLE TRUST AGREEMENT (this \"Agreement\") is made and entered into as of the 3rd day "
            f"of June, 2020, by and between {R} and {C}, husband and wife, each residing in Mecklenburg County, "
            f"North Carolina (each a \"Grantor\" and together the \"Grantors\"), and {RB}, of Mecklenburg County, "
            "North Carolina (the \"Trustee\")."),
          P("RECITALS", ARTICLE),
          P(f"A. The Grantors are the parents of three (3) children: {HENRY['full'].upper()}, born May 9, 2003; "
            f"{OLIVIA['full'].upper()}, born October 30, 2006; and {SAMUEL['full'].upper()}, born January 17, 2010 "
            "(together, the \"Children\" and each a \"Child\").", NOINDENT),
          P("B. The Grantors wish to establish an irrevocable trust for the benefit of the Children and their "
            "descendants, to be known as THE BRADLEY DESCENDANTS IRREVOCABLE TRUST (the \"Trust\").", NOINDENT),
          P("C. Contemporaneously with the execution of this Agreement, the Grantors are transferring to the Trustee "
            "the property described on Schedule A, and the Grantors or others may later transfer additional property "
            "to the Trustee. All such property, together with its income and proceeds, is the \"Trust Estate.\"", NOINDENT),
          P("D. The Trustee is willing to accept the Trust Estate and to hold, administer and distribute it in "
            "accordance with this Agreement.", NOINDENT),
          P("NOW, THEREFORE, the Grantors hereby irrevocably transfer and deliver the Trust Estate to the Trustee, "
            "IN TRUST, to be held upon the following terms:"),
          P("ARTICLE I", ARTICLE), P("NAME, PURPOSE AND TRUST PROPERTY", ARTICLE),
          P("1.1 Name.", SECTION),
          P(f"The Trust shall be known as THE BRADLEY DESCENDANTS IRREVOCABLE TRUST. Property may be titled in the "
            f"name of \"{REBECCA['full']}, Trustee of the Bradley Descendants Irrevocable Trust u/a/d June 3, 2020,\" "
            "or in the name of any successor Trustee then serving."),
          P("1.2 Initial Funding.", SECTION),
          P("The Grantors have delivered to the Trustee the property described on Schedule A, and the Trustee "
            "acknowledges its receipt."),
          P("1.3 Additions.", SECTION),
          P("Any person may add cash, securities, life insurance policies, interests in closely held entities, or "
            "other property acceptable to the Trustee, by lifetime transfer, by will, by beneficiary designation or "
            "otherwise. Additions shall be held under the terms of this Agreement."),
          P("1.4 Purpose.", SECTION),
          P("The purpose of the Trust is to provide for the health, education, maintenance and support of the "
            "Children and their descendants, and to transfer family wealth in a manner consistent with the "
            "Grantors' estate, gift and generation-skipping transfer tax planning."),
          P("ARTICLE II", ARTICLE), P("IRREVOCABILITY", ARTICLE),
          P("2.1 Irrevocable.", SECTION),
          P("This Agreement and the Trust are irrevocable. The Grantors waive every right and power, alone or with "
            "others, to alter, amend, revoke or terminate this Agreement or any trust created under it, or to change "
            "any beneficial interest."),
          P("2.2 No Retained Interest.", SECTION),
          P("No part of the Trust Estate shall revert to or be used for the benefit of either Grantor or to "
            "discharge any legal obligation of either Grantor. <b>Neither Grantor shall serve as Trustee at any "
            "time.</b>"),
          P("2.3 Administrative Amendments.", SECTION),
          P("The Trustee may amend the administrative provisions of this Agreement only to comply with "
            "changes in law, to preserve intended tax treatment, or to correct a scrivener's error, and never to "
            "alter any beneficial interest."),
          P("ARTICLE III", ARTICLE), P("BENEFICIARIES AND SEPARATE SHARES", ARTICLE),
          P("3.1 Beneficiaries.", SECTION),
          P(f"The beneficiaries of the Trust are the Children and their descendants. On the date of this Agreement "
            f"the Children are {HENRY['full'].upper()}, {OLIVIA['full'].upper()} and {SAMUEL['full'].upper()}. "
            "A child later born to or adopted by the Grantors shall be a Child for all purposes."),
          P("3.2 Separate Shares.", SECTION),
          P("The Trustee shall divide the Trust Estate into equal separate shares, one for each Child then living, "
            "and shall administer each share as a separate trust for distribution, accounting and tax purposes. "
            "The Trustee may hold the shares in one consolidated investment account for convenience if the "
            "Trustee keeps records of each share's proportionate interest."),
          P("3.3 Deceased Child.", SECTION),
          P("If a Child dies before full distribution of his or her share, the balance shall pass to that Child's "
            "then-living descendants, per stirpes, or if none, in equal parts to the shares of the other Children."),
          P("ARTICLE IV", ARTICLE), P("WITHDRAWAL RIGHTS", ARTICLE),
          P("4.1 Right of Withdrawal.", SECTION),
          P("Upon each contribution, each Child (or the guardian of a minor Child) may withdraw the lesser of the "
            "Child's pro rata share of the contribution or the federal gift tax annual exclusion amount under "
            "Section 2503(b) of the Internal Revenue Code of 1986, as amended (the \"Code\")."),
          P("4.2 Notice and Lapse.", SECTION),
          P("The Trustee shall promptly notify each Child, or the guardian of a minor Child, of each contribution. "
            "A withdrawal right lapses thirty (30) days after notice, but in any calendar year only to the extent of "
            "the greater of Five Thousand Dollars ($5,000) or five percent (5%) of the Trust Estate; any excess "
            "carries forward to later years."),
          P("ARTICLE V", ARTICLE), P("DISTRIBUTIONS", ARTICLE),
          P("5.1 Discretionary Distributions.", SECTION),
          P("The Trustee may distribute to or for a Child so much of the income and principal of that Child's share "
            "as the Trustee considers advisable for the Child's health, education, maintenance and support. "
            "Undistributed income shall be added to principal at least annually."),
          P("5.2 Education.", SECTION),
          P("The Trustee shall give primary consideration to each Child's educational needs, including tuition, "
            "fees, books, room and board at any secondary school, college, university, graduate or professional "
            "school, or vocational program."),
          P("5.3 Staged Distributions.", SECTION),
          P("When a Child reaches the following ages, the Trustee shall distribute to the Child, free of trust:"),
          P("(a) at age twenty-five (25), one-third (1/3) of the principal of the Child's share;", ITEM),
          P("(b) at age thirty (30), one-half (1/2) of the remaining principal; and", ITEM),
          P("(c) at age thirty-five (35), the entire remaining balance, whereupon the share terminates.", ITEM),
          P("5.4 Deferral.", SECTION),
          P("The Trustee may defer any distribution under Section 5.3 while a Child is the subject of substance "
            "dependency, pending litigation, creditor claims, divorce proceedings or legal incapacity, and shall "
            "document the reason for the deferral in writing."),
          P("ARTICLE VI", ARTICLE), P("TRUSTEE PROVISIONS", ARTICLE),
          P("6.1 Initial Trustee.", SECTION),
          P(f"{RB} shall serve as the initial Trustee of the Trust and of each separate share."),
          P("6.2 Successor Trustees.", SECTION),
          P(f"If {RB} dies, resigns, becomes incapacitated or otherwise ceases to serve, {DW} shall serve as "
            f"successor Trustee. If {DW} is unable or unwilling to serve, the then-serving Trustee, or if none, a "
            "majority of the adult Children, may appoint as successor Trustee any bank or trust company "
            "qualified to conduct trust business in the State of North Carolina."),
          P("6.3 Resignation.", SECTION),
          P("A Trustee may resign by signed written notice delivered to the successor Trustee, to each adult "
            "Child, and to the guardian of each minor Child. The resignation is effective on the date stated in "
            "the notice or, if none, on acceptance by the successor Trustee."),
          P("6.4 Bond; Compensation; Liability.", SECTION),
          P("No Trustee shall be required to post bond. An individual Trustee may receive reasonable compensation; "
            "a corporate Trustee shall be paid under its published fee schedule. No successor Trustee is liable for "
            "the acts of a predecessor or required to audit a predecessor's accounts."),
          P("ARTICLE VII", ARTICLE), P("TRUSTEE POWERS", ARTICLE),
          P("7.1 General Powers.", SECTION),
          P("In addition to the powers conferred by the North Carolina Uniform Trust Code, N.C.G.S. Chapter 36C, the "
            "Trustee may, without court order:"),
          P("(a) retain, buy and sell any kind of property or investment, including interests in closely held "
            "partnerships and limited liability companies;", ITEM),
          P("(b) open, maintain and close accounts with any bank, broker-dealer or custodian, in the name of the "
            "Trust or a nominee, and sign account agreements and transfer instructions;", ITEM),
          P("(c) engage a registered investment adviser and delegate discretionary investment authority to it;", ITEM),
          P("(d) borrow, pledge, vote securities, and participate in reorganizations;", ITEM),
          P("(e) employ attorneys, accountants and agents and pay them from the Trust Estate; and", ITEM),
          P("(f) make distributions in cash or in kind, on a non-pro-rata basis among separate shares.", ITEM),
          P("7.2 Reliance by Third Parties.", SECTION),
          P("A bank, broker-dealer, custodian or transfer agent may rely on a certification of trust signed by the "
            "Trustee then serving and need not inquire into the terms of this Agreement."),
          P("ARTICLE VIII", ARTICLE), P("SPENDTHRIFT PROVISION", ARTICLE),
          P("No beneficiary may anticipate, assign or encumber any interest in the Trust, and no interest shall be "
            "subject to the claims of any creditor, spouse or former spouse of a beneficiary, to the fullest extent "
            "permitted by N.C.G.S. Section 36C-5-502."),
          P("ARTICLE IX", ARTICLE), P("TAX PROVISIONS", ARTICLE),
          P("9.1 Non-Grantor Trust.", SECTION),
          P("The Grantors intend that the Trust be a separate taxpayer and that neither Grantor be treated as owner "
            "of any portion of it under Sections 671 through 679 of the Code. The Trust shall obtain its own "
            "taxpayer identification number."),
          P("9.2 GST Exemption.", SECTION),
          P("The Trustee may divide any trust into separate trusts with inclusion ratios of zero and one to "
            "preserve the benefit of any generation-skipping transfer tax exemption allocated to the Trust."),
          P("ARTICLE X", ARTICLE), P("GENERAL PROVISIONS", ARTICLE),
          P("10.1 Governing Law and Situs.", SECTION),
          P("This Agreement is governed by the laws of the State of North Carolina. The initial situs of the Trust "
            "is Mecklenburg County, North Carolina."),
          P("10.2 Accountings.", SECTION),
          P("The Trustee shall account at least annually to each adult beneficiary and to the guardian of each "
            "minor beneficiary."),
          P("10.3 Definitions.", SECTION),
          P("\"Child\" and \"descendants\" include persons adopted before age eighteen (18). A person is "
            "\"incapacitated\" on the written certification of two (2) licensed physicians."),
          P("10.4 Severability; Counterparts.", SECTION),
          P("If any provision is held invalid, the rest remains in effect. This Agreement may be signed in "
            "counterparts."),
          PageBreak()]

    # ---- signatures
    s += [P("IN WITNESS WHEREOF, the Grantors and the Trustee have signed this Agreement as of the date first "
            "written above.", NOINDENT),
          sig_block("GRANTOR:", R), sig_block("GRANTOR:", C), sig_block("TRUSTEE:", RB),
          Spacer(1, 18), P("ACCEPTANCE BY TRUSTEE", ARTICLE),
          P("The undersigned accepts appointment as Trustee of the Bradley Descendants Irrevocable Trust, "
            "acknowledges receipt of the property described on Schedule A, and agrees to administer the Trust "
            "Estate under this Agreement."),
          sig_block("", f"{RB}, Trustee"),
          PageBreak(),
          P("STATE OF NORTH CAROLINA", NOINDENT), P("COUNTY OF MECKLENBURG", NOINDENT), Spacer(1, 8),
          P(f"On this 3rd day of June, 2020, before me personally appeared {R}, {C} and {RB}, each known to me or "
            "proven by satisfactory evidence to be the persons whose names are signed to the foregoing instrument, "
            "and each acknowledged that he or she signed it voluntarily for its stated purpose.", NOINDENT),
          sig_block("", "Notary Public, State of North Carolina", "My commission expires: August 21, 2023"),
          Spacer(1, 20), P("WITNESSES:", NOINDENT),
          Table([[P("_______________________________", SIG), P("_______________________________", SIG)],
                 [P("Thomas J. Okonkwo", SIG), P("Lauren B. Feldman", SIG)]], colWidths=[3.1 * inch, 3.1 * inch]),
          PageBreak()]

    # ---- schedule A
    sched = Table(
        [["Item", "Description", "Value"],
         ["1.", "Cash", "$10.00"],
         ["2.", "Cash contribution, June 10, 2020", "$60,000.00"],
         ["3.", "1,500 shares of common stock, Quail Hollow Holdings, Inc.", "$412,500.00"],
         ["", "Total Initial Trust Property", "$472,510.00"]],
        colWidths=[0.55 * inch, 4.35 * inch, 1.3 * inch])
    sched.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Times-Roman", 10), ("FONT", (0, 0), (-1, 0), "Times-Bold", 10),
        ("FONT", (0, -1), (-1, -1), "Times-Bold", 10), ("ALIGN", (2, 0), (2, -1), "RIGHT"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.black), ("LINEABOVE", (0, -1), (-1, -1), 0.8, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    s += [P("SCHEDULE A", TITLE), P("Initial Trust Property", SUBTITLE), Spacer(1, 10),
          P("The Grantors have transferred to the Trustee, and the Trustee acknowledges receipt of, the following "
            "property, to be held under the Bradley Descendants Irrevocable Trust Agreement dated June 3, 2020:",
            NOINDENT),
          Spacer(1, 8), sched, Spacer(1, 14),
          P("Custodial account established with J.P. Morgan Securities LLC, Account No. XXX-X7731-0, in the name of "
            "the Bradley Descendants Irrevocable Trust.", NOINDENT),
          sig_block("", f"{RB}, Trustee", "Date: June 3, 2020")]
    doc.go(s)
    return log

