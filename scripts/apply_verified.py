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


def best_match(posting, rows):
    """Closest existing row for a posting: same employer, same city, nearest title."""
    pc, pcity = norm(posting.get("Company")), norm(posting.get("City"))
    ptok = tokens(posting.get("Role_Title"))
    best, best_score = None, 0
    for row in rows:
        rc = norm(row.get("Company"))
        if not rc or not pc:
            continue
        # Employer names vary ("Aldar" vs "Aldar Estates"), so accept containment.
        if not (pc in rc or rc in pc):
            continue
        if pcity and norm(row.get("City")) and pcity not in norm(row.get("City")) \
                and norm(row.get("City")) not in pcity:
            continue
        overlap = len(ptok & tokens(row.get("Role_Title")))
        if overlap > best_score:
            best, best_score = row, overlap
    return best if best_score >= 1 else None


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

    print(f"Verified postings loaded : {len(postings)}")
    print(f"  upgraded existing rows : {upgraded}")
    print(f"  already verified       : {already}")
    print(f"  no matching row        : {len(unmatched)}")
    for p in unmatched:
        print(f"      {p.get('Company')} | {p.get('Role_Title')} | {p.get('City')}  [{p['_src']}]")
    if unmatched:
        print("  ^ these are genuine finds with no row to attach to - add them by hand if they matter.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
