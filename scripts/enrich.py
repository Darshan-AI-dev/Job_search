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


def midpoint(comp):
    m = re.match(r"^\s*(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*$", comp or "")
    if not m:
        return None
    return (float(m.group(1)) + float(m.group(2))) / 2


def comp_check(row, benchmarks):
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

            for c in CORRECTIONS:
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
