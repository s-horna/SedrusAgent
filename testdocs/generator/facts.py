"""Single source of truth for the fictitious Bradley household.

Everything here is invented. SSNs use the never-issued 666 area number.
"""

HOME = ("4410 Quail Hollow Rd", "Charlotte, NC 28210")
HOME_UPPER = ("4410 QUAIL HOLLOW RD", "CHARLOTTE NC 28210")

ROBERT = dict(full="Robert W. Bradley II", ssn="666-41-2087")
CATHERINE = dict(full="Catherine M. Bradley", ssn="666-58-3312")
HENRY = dict(full="Henry R. Bradley", dob="2003-05-09", ssn="666-83-5521")
OLIVIA = dict(full="Olivia C. Bradley", dob="2006-10-30", ssn="666-72-0145")
SAMUEL = dict(full="Samuel T. Bradley", dob="2010-01-17", ssn="666-19-4402")
# The initial trustee. "R. Bradley" collides with Robert.
REBECCA = dict(full="Rebecca L. Bradley", address=("410 Quail Hollow Rd", "Charlotte, NC 28226"))
# Successor trustee named in the trust.
DANIEL = dict(full="Daniel P. Whitaker")

TRUST = dict(
    name="THE BRADLEY DESCENDANTS IRREVOCABLE TRUST",
    short="Bradley Descendants Irrevocable Trust",
    date_long="June 3, 2020",
    date_iso="2020-06-03",
    # The custodian's registration carries a different trust date (conflict trap).
    custodian_dtd="09/14/2016",
    ein="87-3319042",
)

LP = dict(
    name="Bradley Capital Partners, LP",
    upper="BRADLEY CAPITAL PARTNERS, LP",
    address=("200 South Tryon Street, Suite 1450", "Charlotte, NC 28202"),
    address_upper=("200 S TRYON ST STE 1450", "CHARLOTTE NC 28202"),
)

# Accounts -------------------------------------------------------------------
JPM_TRUST_SUMMARY = "448-17731-0"  # consolidated summary portfolio
JPM_TRUST_BRKG = "448-17732-8"     # zero-balance brokerage sub-account
JPM_TRUST_MAIN = "448-17733-6"     # where the assets are
JPM_LP = "448-17740-2"

SCHWAB_ROTH = "4471-8820"
SCHWAB_JOINT = "6612-0094"
MS_ACCTS = [  # Morgan Stanley consolidated JTWROS
    ("228-104477-118", "Active Assets Account", "Brokerage"),
    ("228-104491-118", "Portfolio Management - Select UMA", "Advisory"),
    ("228-104503-118", "Alternative Investments", "Brokerage"),
]
EQUINITI_HOLDER = "0004417220"
