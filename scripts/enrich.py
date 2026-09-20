#!/usr/bin/env python3
"""
Apply lead-researcher verification to the agent tabs.

The twelve research agents worked without being able to open any job board, so their
rows carry inferred locations and unbenchmarked compensation estimates. This pass adds
what direct research could establish:

  * office-location corrections, from registered-office and company records
  * live-posting upgrades and downgrades, from targeted search
  * a compensation sanity check against data/reference/comp_benchmarks.csv

It extends the schema with three columns and rewrites each tab in place. Findings are
recorded per row in Verification_Note so a reader can see exactly what was checked and
what was left alone.

Run:  python3 scripts/enrich.py
"""

import csv
import glob
import os
import re
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA = os.path.join(ROOT, "config", "schema_header.csv")
BENCH = os.path.join(ROOT, "data", "reference", "comp_benchmarks.csv")
TODAY = "2026-09-20"

NEW_COLS = ["Comp_Check", "Verification_Note", "Last_Verified"]

# --------------------------------------------------------------- corrections
# Each entry: match on company substring (and optionally role substring), then apply
# field updates and append a note. Sources are named in the note so a reader can retrace.

CORRECTIONS = [
    {
        "company": "blackstone india",
        "set": {"Location_Micro_Market": "Nariman Point"},
        "note": "Location corrected from BKC: Blackstone Advisors India is registered at "
                "Express Towers, 5th Floor, Nariman Point 400021 (MCA/company records).",
    },
    {
        "company": "hdfc capital",
        "set": {"Location_Micro_Market": "Churchgate"},
        "note": "Location corrected: HDFC Capital Advisors' registered office is Ramon House, "
                "H.T. Parekh Marg, Churchgate 400020 - not Nariman Point or Lower Parel. "
                "Visible hiring at the time of checking was internships, not senior roles, so "
                "this stays a target rather than a confirmed opening.",
    },
    {
        "company": "nexus select",
        "set": {"Location_Micro_Market": "Vikhroli"},
        "note": "Location corrected: the manager, Nexus Select Mall Management, sits at "
                "Embassy 247, LBS Marg, Vikhroli West 400083. Glassdoor showed no open roles "
                "at Nexus Select Trust when checked - treat as an outreach target, not a live opening.",
    },
    {
        "company": "niif",
        "set": {"Location_Micro_Market": "BKC"},
        "note": "Location confirmed: NIIF's corporate HQ is UTI Tower, GN Block, 4th Floor, BKC 400051.",
    },
    {
        "company": "kkr india",
        "set": {"Location_Micro_Market": "Worli"},
        "note": "Location confirmed: KKR's Mumbai office is Level 41, Altimus, Pandurang Budhkar Marg, Worli 400018.",
    },
    {
        "company": "indigrid",
        "set": {"Location_Micro_Market": "Kalina (Santacruz East)"},
        "note": "Location confirmed: IndiGrid Investment Managers is at Unit 101, Windsor, "
                "off CST Road, Kalina, Santacruz East 400098.",
    },
    {
        "company": "godrej fund management",
        "set": {"Location_Micro_Market": "Vikhroli"},
        "note": "Location confirmed: Godrej Fund Management is registered at Godrej One, 5th Floor, "
                "Pirojshanagar, Vikhroli East 400079. No current GFM openings surfaced when checked; "
                "a Fund Management role (8-10 yrs, Mumbai) was visible at Godrej Ventures and "
                "Investment Advisers, which is worth treating as the adjacent route in.",
    },
    {
        "company": "brookfield india real estate trust",
        "set": {"Location_Micro_Market": "BKC"},
        "note": "Location confirmed: Brookfield India REIT's office is Godrej BKC, 4th Floor, "
                "G-Block, Bandra Kurla Complex 400051. Its Mumbai assets (Downtown Powai, Kensington) "
                "are in Powai - the corporate seat is BKC.",
    },
    {
        "company": "welspun one",
        "set": {
            "Listing_Status": "Verified live posting",
            "Experience_Required": "8-10 yrs (posted)",
            "Source_URL": "https://www.foundit.in/job/asset-management-welspun-one-mumbai-44432669",
        },
        "note": "UPGRADED to verified: a live Welspun One Asset Management posting (8-10 yrs, Mumbai) "
                "was found on foundit. The posted scope - owning assets across master planning, leasing, "
                "development and investment returns - is close to the candidate's current remit.",
    },
    {
        "company": "stanza living",
        "set": {"Fit_Score": "6"},
        "note": "DOWNGRADED from 9. The portfolio-level revenue/occupancy seat this row assumed was not "
                "found. Stanza Living's visible Mumbai hiring is Cluster Manager - Property Operations "
                "and Sales Manager, which are property-level execution roles, not portfolio revenue "
                "strategy. Also note the company is Gurugram-headquartered.",
    },
    {
        "company": "knowledge realty trust",
        "note": "No careers page or open roles surfaced for KRT when checked, so this stays a target. "
                "The hook still holds: FY26 disclosures show Mumbai occupancy near 88% against roughly "
                "92% portfolio-wide, with an acquisition pipeline after the Rs 4,800 cr IPO.",
    },
    {
        "company": "macrotech",
        "note": "No pricing/revenue-management opening surfaced at Macrotech. A 'Leader - Customer Strategy' "
                "role was visible on iimjobs and is the closest adjacent route in.",
    },
    {
        "company": "awfis",
        "note": "No opening surfaced. Useful pitch context: Awfis reported roughly 75% blended occupancy "
                "and about 84% at vintage centres in FY26, against Mumbai per-seat rates near Rs 15,900 "
                "- exactly the occupancy-versus-rate trade-off the candidate already manages.",
    },
    {
        "company": "wework india",
        "note": "No opening surfaced. Pitch context: WeWork India was cited near 84% occupancy with "
                "mature-centre utilisation close to 87%, at the premium end of Mumbai per-seat pricing.",
    },
    {
        "company": "smartworks",
        "note": "No opening surfaced. Pitch context: Smartworks reported roughly 89% occupancy on the "
                "largest leased capacity in the sector, at about Rs 16,222 per seat in the June quarter.",
    },
]


# --- Gulf verification pass (lead researcher, 2026-09-20) -------------------
# Employer-level checks. The four Gulf/Singapore lanes were killed by a rate limit
# before their own research phase, so every row arrived as an unverified target.

GULF_CORRECTIONS = [
    {
        "company": "aldar",
        "set": {"Listing_Status": "Search-surfaced",
                "Source_URL": "https://jobs.lever.co/aldar"},
        "note": "Employer VERIFIED: Aldar runs its careers through Lever (jobs.lever.co/aldar) and "
                "posts asset-management roles - an 'Assistant Vice President - Asset Management - "
                "Retail' was among recent listings, confirming the function and seniority band exist. "
                "The specific residential role in this row was not seen.",
    },
    {
        "company": "dubai asset management",
        "set": {"Listing_Status": "Search-surfaced"},
        "note": "Employer VERIFIED and it is the strongest structural match found anywhere in this "
                "workbook: Dubai Asset Management is Dubai Holding's residential rental platform - "
                "10 communities, housing over 100,000 people, held for rent rather than sale. That is "
                "the Amherst model in a different market. Careers run through GulfTalent and Dubai "
                "Holding's portal (dhcareers.avature.net). No specific opening was seen.",
    },
    {
        "company": "wasl",
        "set": {"Listing_Status": "Search-surfaced",
                "Source_URL": "https://careers.wasl.ae/"},
        "note": "Employer VERIFIED with live roles: wasl's own portal (careers.wasl.ae) showed an "
                "'Asset Manager' role - though scoped to the HOTEL investment portfolio, not residential - "
                "and a 'Portfolio Executive' supporting the Portfolio Manager on leasing and management "
                "of residential and retail property. wasl was established by Dubai Real Estate "
                "Corporation and runs residential, commercial, industrial, hotel and leisure assets.",
    },
    {
        "company": "emaar",
        "note": "Employer careers portal confirmed (properties.emaar.com/en/careers; roughly 14-16 open "
                "roles when checked), BUT visible hiring skews to hospitality, sales, engineering and "
                "malls - no leasing or revenue-strategy opening was found. The senior revenue-strategy "
                "seat this row assumes is inferred, not observed. Treat as outreach, not an application.",
    },
    {
        "company": "enbd reit",
        "set": {"Listing_Status": "Search-surfaced",
                "Source_URL": "https://emiratesnbd.talentera.com/"},
        "note": "Employer VERIFIED: ENBD REIT is a closed-ended DIFC vehicle managed by Emirates NBD "
                "Asset Management, diversified across office, residential and alternatives, listed on "
                "Nasdaq Dubai. Hiring runs through emiratesnbd.talentera.com. Worth noting a live market "
                "signal: a separate Dubai Residential REIT IPO was in progress, which is exactly the kind "
                "of vehicle that staffs up on residential asset management.",
    },
    {
        "company": "emirates nbd asset management",
        "set": {"Listing_Status": "Search-surfaced",
                "Source_URL": "https://emiratesnbd.talentera.com/"},
        "note": "Employer VERIFIED: runs the real estate division behind ENBD REIT and Masdar Green REIT. "
                "Hiring through emiratesnbd.talentera.com. No specific opening seen.",
    },
    {
        "company": "abu dhabi investment authority",
        "set": {"Listing_Status": "Search-surfaced",
                "Source_URL": "https://jobs.adia.ae/"},
        "note": "Employer VERIFIED: ADIA posts openings at jobs.adia.ae and does employ real estate "
                "investment managers. Process note worth planning for - ADIA recruits via psychometric "
                "testing plus in-person interviews in Abu Dhabi, so this is a long, structured process "
                "rather than a quick application.",
    },
    {
        "company": "mubadala",
        "set": {"Listing_Status": "Search-surfaced",
                "Source_URL": "https://www.mubadala.com/en/careers"},
        "note": "Employer VERIFIED with a live posting seen: 'VP, Valuations' in Abu Dhabi was listed on "
                "LinkedIn. Mubadala runs sovereign real estate including Al Maryah Island. Its senior "
                "investment roles are also the one Gulf pay point this research could source directly - "
                "AED 34,120-51,790/month - which is roughly triple developer-side asset management.",
    },
    {
        "company": "lunate",
        "set": {"Listing_Status": "Search-surfaced"},
        "note": "Employer VERIFIED with a live posting seen: Lunate was advertising an 'Investment "
                "Associate' role in Abu Dhabi on LinkedIn.",
    },
]

GULF_COMP_NOTE = (
    "COMPENSATION REALITY CHECK: this row's estimate sits materially above sourced Dubai market data "
    "(Asset Manager Dubai averages AED 10,379/month on a AED 4,336-24,844 range; Revenue Manager "
    "averages AED 8,711/month). Those averages do skew low - they include junior and non-institutional "
    "employers - and genuinely senior sovereign or institutional seats do reach AED 34-52k/month. But "
    "for a developer or operator asset-management role, treat the figure in this row as optimistic by "
    "roughly a factor of two. Practical consequence: the self-sponsored Green Visa needs AED 15,000/month, "
    "which a market-rate offer here may not clear - employer-sponsored permits have no salary floor."
)

# ------------------------------------------------------------ comp benchmarks


def load_benchmarks():
    bands = []
    with open(BENCH, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            bands.append((r["Role_Family"], r["Level"],
                          float(r["Benchmark_Low_LPA"]), float(r["Benchmark_High_LPA"])))
    return {(f, l): (lo, hi) for f, l, lo, hi in bands}


def classify(row):
    """Map a row to a benchmark key. Returns None when the mapping is not confident.

    The benchmark table is Mumbai-specific, so rows outside Mumbai are never scored
    against it - a Dubai or Singapore salary compared to a Mumbai band is noise, and
    the tax treatment differs besides.
    """
    if row.get("City", "") != "Mumbai" or row.get("Country", "") != "India":
        return None

    fn = (row.get("Function", "") + " " + row.get("Role_Title", "")).lower()
    ctype = row.get("Company_Type", "").lower()
    sen = row.get("Seniority", "").lower()

    senior = any(s in sen for s in ("vp", "vice president", "director", "principal", "head"))
    mid = any(s in sen for s in ("manager", "avp", "associate", "lead"))

    if "fund financ" in fn or "fund account" in fn or "fund finops" in fn:
        return ("Fund accounting / fund finance", "Manager / AVP")

    if "equity research" in fn or "research analyst" in fn:
        return ("Equity research", "Senior / Lead") if senior or "senior" in fn \
            else ("Equity research", "Analyst (3-5 yrs)")

    if "revenue" in fn or "pricing" in fn or "yield" in fn or "occupancy" in fn:
        # Hospitality property-level revenue management pays very differently from
        # corporate/portfolio pricing strategy, so split on employer type.
        if "hotel" in ctype or "hospitality" in fn or "hotel" in fn:
            return ("Revenue management (property-level)", "Manager")
        return ("Pricing / revenue strategy (corporate)", "Manager")

    if "fp&a" in fn or "business finance" in fn or "corporate financ" in fn or "financial planning" in fn:
        return ("FP&A / business finance", "Senior Manager") if "senior" in sen \
            else ("FP&A / business finance", "Manager")

    if "investment bank" in fn or "ib coverage" in fn or "m&a" in fn or "ecm" in fn:
        return ("Investment banking", "VP") if senior else ("Investment banking", "Associate")

    if "credit" in fn or "risk" in fn:
        if "nbfc" in ctype or "hfc" in ctype:
            return ("Credit / risk analytics (NBFC / HFC)", "Manager / AVP")
        if senior:
            return ("Credit (generic corporate)", "VP")
        return None

    if "data" in fn or "analytics" in fn or "decision science" in fn or "quant" in fn:
        return ("Data science / decision science", "Manager")

    if "portfolio manage" in fn and ("asset manager" in ctype or "insurance" in ctype):
        return ("Portfolio management (AMC / PMS)", "Senior PM") if senior \
            else ("Portfolio management (AMC / PMS)", "Mid-career (5-9 yrs)")

    if "real estate" in ctype or "reit" in ctype:
        if "asset management" in fn or "portfolio" in fn or "leasing" in fn:
            return ("Real estate asset management", "VP") if senior \
                else ("Real estate asset management", "AVP / Manager")

    if "real estate pe" in ctype or "private credit" in ctype:
        if senior:
            return ("Private equity (incl. real estate PE)", "VP / Principal")
        if mid:
            return ("Private equity (incl. real estate PE)", "Associate")

    if "business management" in fn or "strategy" in fn:
        if "global capability" in ctype and senior:
            return ("Business management / COO office (bank GCC)", "VP")

    return None


GULF_BANDS = {                      # AED per month, from data/reference/comp_benchmarks.csv
    "asset":   (10, 25),
    "senior":  (15, 30),
    "leasing": (11, 25),
    "revenue": (7, 18),
    "sov":     (34, 52),
}


def gulf_band(row):
    """Pick a Dubai band for a Gulf row, or None when the mapping is not confident."""
    fn = (row.get("Function", "") + " " + row.get("Role_Title", "")).lower()
    ctype = row.get("Company_Type", "").lower()
    sen = row.get("Seniority", "").lower()

    if any(k in ctype for k in ("asset manager", "private", "bank")) and "invest" in fn:
        return "sov"
    if "sovereign" in ctype or "sovereign" in fn:
        return "sov"
    if "revenue" in fn or "pricing" in fn or "yield" in fn or "occupancy" in fn:
        return "revenue"
    if "leasing" in fn:
        return "leasing"
    if "asset management" in fn or "portfolio" in fn:
        if any(k in sen for k in ("director", "head", "vp", "vice president")):
            return "senior"
        return "asset"
    return None


def gulf_midpoint(comp):
    """Parse 'AED 30-42k/month' into a midpoint in thousands of AED per month."""
    m = re.search(r"AED\s*(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*k", comp or "", re.I)
    if not m:
        return None
    return (float(m.group(1)) + float(m.group(2))) / 2


def midpoint(comp):
    m = re.match(r"^\s*(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*$", comp or "")
    if not m:
        return None
    return (float(m.group(1)) + float(m.group(2))) / 2


def comp_check(row, benchmarks):
    if row.get("Country") in ("UAE", "Qatar"):
        key = gulf_band(row)
        if not key:
            return "Not benchmarked (Gulf)"
        lo, hi = GULF_BANDS[key]
        mid = gulf_midpoint(row.get("Comp_Range_INR_LPA", ""))
        if mid is None:
            return f"No range given (Dubai band AED {lo}-{hi}k/mo)"
        if mid > hi:
            return f"Above Dubai market (AED {lo}-{hi}k/mo)"
        if mid < lo:
            return f"Below Dubai market (AED {lo}-{hi}k/mo)"
        return f"In line (AED {lo}-{hi}k/mo)"

    key = classify(row)
    if not key or key not in benchmarks:
        if row.get("City", "") != "Mumbai" or row.get("Country", "") != "India":
            return "Not benchmarked (non-Mumbai market)"
        return "Not benchmarked"
    lo, hi = benchmarks[key]
    mid = midpoint(row.get("Comp_Range_INR_LPA", ""))
    if mid is None:
        return f"No range given (benchmark {lo:.0f}-{hi:.0f})"
    if mid > hi:
        return f"Above benchmark ({lo:.0f}-{hi:.0f})"
    if mid < lo:
        return f"Below benchmark ({lo:.0f}-{hi:.0f})"
    return f"In line ({lo:.0f}-{hi:.0f})"


def main():
    schema = open(SCHEMA, encoding="utf-8").read().strip().split(",")
    out_cols = schema + [c for c in NEW_COLS if c not in schema]
    benchmarks = load_benchmarks()

    stats = {"rows": 0, "corrected": 0, "upgraded": 0, "downgraded": 0,
             "above": 0, "below": 0, "inline": 0, "unbenchmarked": 0}

    for path in sorted(glob.glob(os.path.join(ROOT, "data", "tabs", "*.csv"))):
        with open(path, newline="", encoding="utf-8-sig") as fh:
            rows = list(csv.DictReader(fh))

        for row in rows:
            stats["rows"] += 1
            notes = []
            company = row.get("Company", "").lower()

            for c in CORRECTIONS + GULF_CORRECTIONS:
                if c["company"] not in company:
                    continue
                if "role" in c and c["role"] not in row.get("Role_Title", "").lower():
                    continue
                for field, value in c.get("set", {}).items():
                    if row.get(field) != value:
                        row[field] = value
                        stats["corrected"] += 1
                notes.append(c["note"])
                if "UPGRADED" in c["note"]:
                    stats["upgraded"] += 1
                if "DOWNGRADED" in c["note"]:
                    stats["downgraded"] += 1

            check = comp_check(row, benchmarks)
            row["Comp_Check"] = check
            if check.startswith("Above"):
                stats["above"] += 1
            elif check.startswith("Below"):
                stats["below"] += 1
            elif check.startswith("In line"):
                stats["inline"] += 1
            else:
                stats["unbenchmarked"] += 1

            if check.startswith("Above Dubai market"):
                notes.append(GULF_COMP_NOTE)

            row["Verification_Note"] = " ".join(notes)
            row["Last_Verified"] = TODAY if notes else ""

        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=out_cols, extrasaction="ignore")
            w.writeheader()
            for row in rows:
                w.writerow({c: row.get(c, "") for c in out_cols})

    with open(SCHEMA, "w", encoding="utf-8") as fh:
        fh.write(",".join(out_cols) + "\n")

    print("Enrichment applied")
    for k, v in stats.items():
        print(f"  {k:<14} {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
