#!/usr/bin/env python3
"""
Fold verified live postings back into the research tabs.

Verification agents write `data/reference/verified_postings_*.csv` — a flat list of
postings they could actually confirm. This script matches each one against the
existing rows and upgrades them in place: Listing_Status becomes a verified live
posting, the real requisition URL replaces the standing search link, and the
evidence is recorded so a reader can see what was actually seen.

A posting that matches nothing is reported rather than silently dropped, so a genuine
find is never lost just because no lane happened to guess that exact title.

Run:  python3 scripts/apply_verified.py
"""

import csv
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA = open(os.path.join(ROOT, "config", "schema_header.csv")).read().strip().split(",")


CITY_TO_COUNTRY = {
    "dubai": "UAE", "abu dhabi": "UAE", "doha": "Qatar", "riyadh": "Saudi Arabia",
    "singapore": "Singapore", "mumbai": "India", "bengaluru": "India", "gurugram": "India",
    "hyderabad": "India", "pune": "India", "chennai": "India", "luxembourg": "Luxembourg",
    "dublin": "Ireland", "amsterdam": "Netherlands", "frankfurt": "Germany",
    "sydney": "Australia", "melbourne": "Australia", "auckland": "New Zealand",
    "nairobi": "Kenya",
}


def country_for(city):
    """Postings files carry a city but no country; the workbook filters on country."""
    low = (city or "").lower()
    for key, value in CITY_TO_COUNTRY.items():
        if key in low:
            return value
    return ""


def norm(text):
    return re.sub(r"[^a-z0-9]+", "", (text or "").lower())


def tokens(text):
    return {t for t in re.split(r"[^a-z0-9]+", (text or "").lower()) if len(t) > 3}


def load_postings():
    out = []
    for path in sorted(glob.glob(os.path.join(ROOT, "data", "reference", "verified_postings_*.csv"))):
        with open(path, newline="", encoding="utf-8-sig") as fh:
            for p in csv.DictReader(fh):
                if p.get("Company") and p.get("Role_Title"):
                    p["_src"] = os.path.basename(path)
                    out.append(p)
    return out


GENERIC = {"manager", "senior", "vice", "president", "director", "head", "lead",
           "associate", "analyst", "executive", "assistant", "officer", "specialist"}

# A posting only verifies a row if it is also the same GRADE. Matching a VP row to
# an analyst posting would claim a senior seat is open on the evidence of a junior one.
SENIORITY_RANK = (
    ("principal", 6), ("head", 6), ("director", 6), ("vice president", 5), ("vp", 5),
    ("avp", 4), ("senior manager", 4), ("manager", 3), ("senior associate", 2),
    ("senior analyst", 2), ("associate", 2), ("analyst", 1), ("executive", 1),
)


def rank(text):
    """Grade of a title or seniority label, 0 when it cannot be read."""
    low = (text or "").lower()
    for word, value in SENIORITY_RANK:
        if word in low:
            return value
    return 0


def grades_compatible(posting, row):
    p = rank(posting.get("Seniority")) or rank(posting.get("Role_Title"))
    r = rank(row.get("Seniority")) or rank(row.get("Role_Title"))
    if not p or not r:
        return True          # unreadable grade on either side - let the title test decide
    return abs(p - r) <= 1


def distinctive(title):
    """Title tokens that actually identify the job, not the grade."""
    return {t for t in re.split(r"[^a-z0-9]+", (title or "").lower())
            if len(t) > 3 and t not in GENERIC}


def best_match(posting, rows):
    """Find an existing row that is genuinely THE SAME JOB as this posting.

    An earlier version matched on any single shared token, which let a
    'Strategic Planning' posting verify a 'Residential Leasing' row - the same
    employer and grade, an entirely different job. Verification has to mean the
    posting IS the row, so the bar is: same employer, same city, and either an
    identical normalised title or at least two shared distinctive tokens.
    Anything weaker is reported as unmatched and added as its own row instead.
    """
    pc, pcity = norm(posting.get("Company")), norm(posting.get("City"))
    ptitle, ptok = norm(posting.get("Role_Title")), distinctive(posting.get("Role_Title"))
    best, best_score = None, 0
    for row in rows:
        rc = norm(row.get("Company"))
        if not rc or not pc or not (pc in rc or rc in pc):
            continue
        rcity = norm(row.get("City"))
        if pcity and rcity and pcity not in rcity and rcity not in pcity:
            continue
        if not grades_compatible(posting, row):
            continue
        rtitle = norm(row.get("Role_Title"))
        if rtitle == ptitle:
            return row
        overlap = len(ptok & distinctive(row.get("Role_Title")))
        if overlap >= 2 and overlap > best_score:
            best, best_score = row, overlap
    return best


def main():
    postings = load_postings()
    if not postings:
        print("No verified_postings_*.csv found — nothing to apply.")
        return 0

    tabs = {}
    for path in sorted(glob.glob(os.path.join(ROOT, "data", "tabs", "*.csv"))):
        with open(path, newline="", encoding="utf-8-sig") as fh:
            tabs[path] = list(csv.DictReader(fh))

    all_rows = [(path, row) for path, rows in tabs.items() for row in rows]
    flat = [row for _, row in all_rows]
    owner = {id(row): path for path, row in all_rows}

    upgraded, unmatched, already = 0, [], 0
    touched = set()

    for p in postings:
        row = best_match(p, flat)
        if not row:
            unmatched.append(p)
            continue
        if row.get("Listing_Status") == "Verified live posting":
            already += 1
            continue

        row["Listing_Status"] = "Verified live posting"
        if str(p.get("Source_URL", "")).startswith("http"):
            row["Source_URL"] = p["Source_URL"]
        if p.get("Posting_Date") and p["Posting_Date"] != "Unknown":
            row["Posting_Date"] = p["Posting_Date"]
        if p.get("Experience_Required"):
            row["Experience_Required"] = p["Experience_Required"]

        note = (f"UPGRADED to verified live posting on a later verification pass. "
                f"Posting seen: {p.get('Role_Title')} at {p.get('Company')}"
                f"{', ' + p['City'] if p.get('City') else ''}. "
                f"Evidence: {p.get('Evidence', 'not recorded')}")
        existing = row.get("Verification_Note", "")
        row["Verification_Note"] = (existing + " " + note).strip() if existing else note
        row["Last_Verified"] = "2026-09-21"
        upgraded += 1
        touched.add(owner[id(row)])

    for path in touched:
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=SCHEMA, extrasaction="ignore")
            w.writeheader()
            for row in tabs[path]:
                w.writerow({c: row.get(c, "") for c in SCHEMA})

    # A verified posting that matches no row is still real data. Add it as its own
    # row in a dedicated tab rather than forcing it onto an approximate match.
    if unmatched:
        extra = os.path.join(ROOT, "data", "tabs", "25_verified_live_postings.csv")
        existing = []
        if os.path.exists(extra):
            with open(extra, newline="", encoding="utf-8-sig") as fh:
                existing = list(csv.DictReader(fh))
        have = {(norm(r.get("Company")), norm(r.get("Role_Title"))) for r in existing}
        added = 0
        for p in unmatched:
            key = (norm(p.get("Company")), norm(p.get("Role_Title")))
            if key in have:
                continue
            have.add(key)
            row = {c: "" for c in SCHEMA}
            row.update({
                "Listing_ID": f"VP-{len(existing) + added + 1:03d}",
                "Role_Title": p.get("Role_Title", ""),
                "Company": p.get("Company", ""),
                "Company_Type": "Unclassified",
                "Country": p.get("Country") or country_for(p.get("City")),
                "City": p.get("City", ""),
                "Location_Micro_Market": p.get("City", ""),
                "Seniority": p.get("Seniority", ""),
                "Experience_Required": p.get("Experience_Required", "Unknown"),
                "Function": "See role title",
                "Comp_Range_INR_LPA": "Not disclosed",
                "Comp_Basis": "Unknown",
                "Portal": "Verification pass",
                "Source_URL": p.get("Source_URL", ""),
                "Listing_Status": "Verified live posting",
                "Posting_Date": p.get("Posting_Date", "Unknown"),
                "Date_Found": "2026-09-21",
                "Fit_Score": "6",
                "Fit_Rationale": "Found by direct posting search rather than by a research lane, so it is "
                                 "not fit-scored against the profile - read the title and judge it yourself.",
                "Profile_Hook": "",
                "Application_Notes": "Added from a verification sweep because it matched no existing row. "
                                     "Real and live, but unscored and unclassified.",
                "Agent_Source": "VERIFIED",
                "Verification_Note": f"Evidence: {p.get('Evidence', 'not recorded')}",
                "Last_Verified": "2026-09-21",
            })
            existing.append(row)
            added += 1
        if added:
            with open(extra, "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=SCHEMA, extrasaction="ignore")
                w.writeheader()
                for r in existing:
                    w.writerow({c: r.get(c, "") for c in SCHEMA})
            print(f"  added as new rows     : {added} (data/tabs/25_verified_live_postings.csv)")

    print(f"Verified postings loaded : {len(postings)}")
    print(f"  upgraded existing rows : {upgraded}")
    print(f"  already verified       : {already}")
    print(f"  no matching row        : {len(unmatched)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
