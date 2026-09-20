#!/usr/bin/env python3
"""
Merge the per-agent CSV tabs in data/tabs/ into a single formatted Excel workbook.

Each research agent writes one CSV conforming to config/schema_header.csv. This script
validates every file against that schema, then assembles:

    00_START_HERE   orientation, column legend, honest provenance note
    01_MASTER       every row from every agent, ranked by fit
    02_TOP_TARGETS  the high-fit subset worth working first
    03_DASHBOARD    counts by sector, function, portal, evidence status and fit band
    04..15          one tab per research agent, untouched

Run:  python3 scripts/build_workbook.py
"""

import csv
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import date

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABS_DIR = os.path.join(ROOT, "data", "tabs")
SCHEMA = os.path.join(ROOT, "config", "schema_header.csv")
OUT = os.path.join(ROOT, "Mumbai_Finance_Jobs_Master.xlsx")

# ---------------------------------------------------------------- palette

NAVY = "1F3864"
SLATE = "2F5496"
WHITE = "FFFFFF"
BAND = "F2F5FA"

FIT_FILLS = {                      # fit band -> (fill, font colour)
    "high": ("C6E0B4", "1B3A1B"),  # 9-10  direct hit
    "good": ("E2F0D9", "1B3A1B"),  # 7-8   strong adjacency
    "mid": ("FFF2CC", "5A4500"),   # 5-6   transferable
    "low": ("F2F2F2", "808080"),   # 1-4   weak
}

STATUS_FILLS = {
    "Verified live posting": ("C6E0B4", "1B3A1B"),
    "Search-surfaced": ("FFF2CC", "5A4500"),
    "Target employer - not verified": ("F2F2F2", "5A5A5A"),
}

THIN = Side(style="thin", color="D9D9D9")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

# Column display widths, keyed by schema column name.
WIDTHS = {
    "Listing_ID": 11, "Role_Title": 38, "Company": 26, "Company_Type": 20,
    "Location_Micro_Market": 18, "Seniority": 14, "Experience_Required": 16,
    "Function": 20, "Key_Skills": 44, "Comp_Range_INR_LPA": 16, "Comp_Basis": 15,
    "Portal": 18, "Source_URL": 42, "Listing_Status": 26, "Posting_Date": 13,
    "Date_Found": 12, "Fit_Score": 10, "Fit_Rationale": 52, "Profile_Hook": 40,
    "Application_Notes": 52, "Agent_Source": 12, "Duplicate_Of": 13,
}

WRAP_COLS = {"Key_Skills", "Fit_Rationale", "Profile_Hook", "Application_Notes", "Role_Title"}


def fit_band(score):
    try:
        s = int(float(score))
    except (TypeError, ValueError):
        return "low"
    if s >= 9:
        return "high"
    if s >= 7:
        return "good"
    if s >= 5:
        return "mid"
    return "low"


def norm(text):
    """Loose key for duplicate detection across tabs."""
    return re.sub(r"[^a-z0-9]+", "", (text or "").lower())


def load_schema():
    with open(SCHEMA, newline="", encoding="utf-8") as fh:
        return next(csv.reader(fh))


def load_tabs(schema):
    """Return [(slug, [row dicts])] for every CSV present, and a list of problems found."""
    tabs, problems = [], []
    if not os.path.isdir(TABS_DIR):
        return tabs, ["data/tabs/ does not exist"]

    for fname in sorted(os.listdir(TABS_DIR)):
        if not fname.endswith(".csv"):
            continue
        path = os.path.join(TABS_DIR, fname)
        slug = fname[:-4]
        with open(path, newline="", encoding="utf-8-sig") as fh:
            rows = list(csv.DictReader(fh))

        if not rows:
            problems.append(f"{fname}: empty, skipped")
            continue

        got = list(rows[0].keys())
        if got != schema:
            missing = [c for c in schema if c not in got]
            extra = [c for c in got if c not in schema]
            problems.append(f"{fname}: header mismatch (missing={missing} extra={extra})")
            # Coerce onto the canonical schema rather than dropping the agent's work.
            rows = [{c: (r.get(c) or "") for c in schema} for r in rows]

        if len(rows) < 40:
            problems.append(f"{fname}: only {len(rows)} rows (target 40-50)")

        bad_url = sum(1 for r in rows if not str(r.get("Source_URL", "")).startswith("http"))
        if bad_url:
            problems.append(f"{fname}: {bad_url} rows with a non-http Source_URL")

        tabs.append((slug, rows))

    return tabs, problems


def mark_duplicates(all_rows):
    """Annotate cross-tab repeats. First occurrence stays blank; repeats point back to it."""
    seen = {}
    for row in all_rows:
        key = (norm(row.get("Company")), norm(row.get("Role_Title")))
        if key in seen:
            row["Duplicate_Of"] = seen[key]
        else:
            seen[key] = row.get("Listing_ID", "")
            row["Duplicate_Of"] = ""
    return all_rows


def style_header(ws, ncols, row=1, fill=NAVY):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = PatternFill("solid", fgColor=fill)
        cell.font = Font(bold=True, color=WHITE, size=10)
        cell.alignment = Alignment(vertical="center", horizontal="left", wrap_text=True)
    ws.row_dimensions[row].height = 30


def write_grid(ws, columns, rows, freeze="B2", banded=True):
    ws.append(columns)
    style_header(ws, len(columns))

    for i, row in enumerate(rows):
        ws.append([row.get(c, "") for c in columns])
        excel_row = i + 2

        for j, col in enumerate(columns, start=1):
            cell = ws.cell(row=excel_row, column=j)
            cell.border = BORDER
            cell.font = Font(size=10)
            cell.alignment = Alignment(
                vertical="top", wrap_text=col in WRAP_COLS, horizontal="left"
            )
            if banded and i % 2 == 1:
                cell.fill = PatternFill("solid", fgColor=BAND)

            if col == "Fit_Score":
                bg, fg = FIT_FILLS[fit_band(row.get("Fit_Score"))]
                cell.fill = PatternFill("solid", fgColor=bg)
                cell.font = Font(size=10, bold=True, color=fg)
                cell.alignment = Alignment(horizontal="center", vertical="top")
                try:
                    cell.value = int(float(row.get("Fit_Score")))
                except (TypeError, ValueError):
                    pass

            elif col == "Listing_Status":
                bg, fg = STATUS_FILLS.get(str(row.get("Listing_Status", "")).strip(), (None, None))
                if bg:
                    cell.fill = PatternFill("solid", fgColor=bg)
                    cell.font = Font(size=10, color=fg)

            elif col == "Source_URL":
                url = str(row.get("Source_URL", ""))
                if url.startswith("http"):
                    cell.hyperlink = url
                    cell.font = Font(size=10, color="0563C1", underline="single")

            elif col == "Duplicate_Of" and row.get("Duplicate_Of"):
                cell.font = Font(size=10, color="C00000", italic=True)

    for j, col in enumerate(columns, start=1):
        ws.column_dimensions[get_column_letter(j)].width = WIDTHS.get(col, 18)

    ws.freeze_panes = freeze
    if rows:
        ws.auto_filter.ref = f"A1:{get_column_letter(len(columns))}{len(rows) + 1}"
    return ws


def build_readme(wb, tabs, all_rows, problems):
    ws = wb.create_sheet("00_START_HERE")
    ws.sheet_properties.tabColor = NAVY

    def line(text="", *, size=10, bold=False, color="000000", height=None):
        r = ws.max_row + 1 if ws.max_row > 1 or ws["A1"].value else 1
        cell = ws.cell(row=r, column=1, value=text)
        cell.font = Font(size=size, bold=bold, color=color)
        cell.alignment = Alignment(vertical="top", wrap_text=True)
        if height:
            ws.row_dimensions[r].height = height
        return r

    line("Mumbai Finance Job Search — Master Workbook", size=18, bold=True, color=NAVY, height=26)
    line(f"Built {date.today().isoformat()}  ·  {len(all_rows)} rows across {len(tabs)} research tabs",
         size=11, color="595959")
    line()
    line("HOW THIS WAS BUILT", size=12, bold=True, color=SLATE)
    line("Twelve independent research agents each worked one lane of the Mumbai finance market — a "
         "different job family and a different mix of job portals — and each filled its own tab. "
         "Their prompts are version-controlled in agents/prompts/ so any lane can be re-run on its own.")
    line()
    line("READ THIS BEFORE YOU TRUST A ROW", size=12, bold=True, color="C00000")
    line("The research machine could reach a web search index but was blocked by its network proxy "
         "from opening Naukri, LinkedIn, Glassdoor, Indeed, iimjobs, eFinancialCareers and corporate "
         "career sites directly. Agents could therefore see what search returned about a role, but "
         "could not open the posting itself to confirm it. The Listing_Status column records exactly "
         "how much evidence sits behind each row. Treat it as the trust dial and check the live "
         "posting before you invest time in an application.")
    line()
    line("LISTING_STATUS LEGEND", size=12, bold=True, color=SLATE)
    line("Verified live posting  —  search results showed this specific role at this specific firm, "
         "with enough detail to be confident it exists.")
    line("Search-surfaced  —  search indicates the firm is hiring for this kind of role in Mumbai, "
         "but the individual posting was not opened. Confirm before applying.")
    line("Target employer - not verified  —  a well-founded target based on the firm's Mumbai "
         "presence and hiring pattern. No live posting evidence. Treat as an outreach lead, not a listing.")
    line()
    line("FIT_SCORE RUBRIC", size=12, bold=True, color=SLATE)
    line("9-10  Direct hit — revenue/portfolio management, asset strategy, fund & JV capital planning "
         "or distribution modelling at a real estate investment platform, REIT/InvIT, RE PE fund or "
         "residential operator.")
    line("7-8   Strong adjacency — RE-linked FP&A or strategy, fund finance and distributions at an "
         "alternatives GCC, RE/infra banking or research, pricing and yield management outside real estate.")
    line("5-6   Transferable but sideways — general corporate FP&A, business finance or strategy at a "
         "financial institution or GCC.")
    line("3-4   Weak — the title reads finance, the work is accounting, audit, ops or compliance.")
    line("1-2   Off-profile — recorded only where there was a specific reason to note it.")
    line()
    line("TAB GUIDE", size=12, bold=True, color=SLATE)
    line("01_MASTER        every row, ranked by fit score. Start here. Duplicate_Of flags a role "
         "another tab already reported, so you can hide repeats with the filter.")
    line("02_TOP_TARGETS   fit score 8 and above — the shortlist worth working first.")
    line("03_DASHBOARD     the shape of the market: counts by sector, function, portal, evidence "
         "status and fit band.")
    line("04 onwards       one tab per research agent, exactly as that agent filled it.")
    line()
    line("HOW TO WORK IT", size=12, bold=True, color=SLATE)
    line("1. Sort 02_TOP_TARGETS by Listing_Status, then work 'Verified live posting' first.")
    line("2. For each row, Profile_Hook is the experience to lead with and Application_Notes is the "
         "angle, the gap to pre-empt, or the recruiter to approach.")
    line("3. Tab 12 is an outreach map as much as a job list — Mumbai's senior alternatives and "
         "private credit seats move through search firms, not job boards.")
    line("4. Re-run any lane by feeding its prompt file in agents/prompts/ to a fresh agent, then "
         "rebuild with: python3 scripts/build_workbook.py")

    if problems:
        line()
        line("BUILD WARNINGS", size=12, bold=True, color="C00000")
        for p in problems:
            line(f"  · {p}", color="843C0C")

    ws.column_dimensions["A"].width = 118
    return ws


def build_dashboard(wb, all_rows):
    ws = wb.create_sheet("03_DASHBOARD")
    ws.sheet_properties.tabColor = SLATE

    def block(title, counter, start_col, total=None):
        ws.cell(row=1, column=start_col, value=title).font = Font(bold=True, size=11, color=WHITE)
        ws.cell(row=1, column=start_col).fill = PatternFill("solid", fgColor=NAVY)
        ws.cell(row=1, column=start_col + 1).fill = PatternFill("solid", fgColor=NAVY)
        ws.cell(row=1, column=start_col).alignment = Alignment(vertical="center")
        denom = total or sum(counter.values()) or 1
        for i, (key, count) in enumerate(counter.most_common(), start=2):
            ws.cell(row=i, column=start_col, value=key or "(blank)").font = Font(size=10)
            c = ws.cell(row=i, column=start_col + 1, value=count)
            c.font = Font(size=10, bold=True)
            c.alignment = Alignment(horizontal="center")
            ws.cell(row=i, column=start_col + 2, value=round(count / denom, 3)).number_format = "0.0%"
        ws.column_dimensions[get_column_letter(start_col)].width = 32
        ws.column_dimensions[get_column_letter(start_col + 1)].width = 8
        ws.column_dimensions[get_column_letter(start_col + 2)].width = 8

    bands = Counter()
    for r in all_rows:
        b = fit_band(r.get("Fit_Score"))
        bands[{"high": "9-10 Direct hit", "good": "7-8 Strong adjacency",
               "mid": "5-6 Transferable", "low": "1-4 Weak"}[b]] += 1

    block("Evidence status", Counter(r.get("Listing_Status", "") for r in all_rows), 1)
    block("Fit band", bands, 5)
    block("Employer type", Counter(r.get("Company_Type", "") for r in all_rows), 9)
    block("Function", Counter(r.get("Function", "") for r in all_rows), 13)
    block("Portal / channel", Counter(r.get("Portal", "") for r in all_rows), 17)
    block("Micro-market", Counter(r.get("Location_Micro_Market", "") for r in all_rows), 21)
    block("Seniority", Counter(r.get("Seniority", "") for r in all_rows), 25)
    block("Most-cited employers", Counter(r.get("Company", "") for r in all_rows), 29)

    ws.freeze_panes = "A2"
    return ws


def main():
    schema = load_schema()
    tabs, problems = load_tabs(schema)
    if not tabs:
        print("No agent CSVs found in data/tabs/ — nothing to build.", file=sys.stderr)
        return 1

    all_rows = []
    for slug, rows in tabs:
        all_rows.extend(rows)

    all_rows = mark_duplicates(all_rows)
    master_cols = schema + ["Duplicate_Of"]

    def sort_key(r):
        try:
            score = -int(float(r.get("Fit_Score")))
        except (TypeError, ValueError):
            score = 0
        status_rank = {"Verified live posting": 0, "Search-surfaced": 1}.get(
            str(r.get("Listing_Status", "")).strip(), 2
        )
        return (score, status_rank, r.get("Company", ""))

    ranked = sorted(all_rows, key=sort_key)
    top = [r for r in ranked if _score(r) >= 8]

    wb = Workbook()
    wb.remove(wb.active)

    build_readme(wb, tabs, all_rows, problems)

    ws = wb.create_sheet("01_MASTER")
    ws.sheet_properties.tabColor = SLATE
    write_grid(ws, master_cols, ranked)

    ws = wb.create_sheet("02_TOP_TARGETS")
    ws.sheet_properties.tabColor = "70AD47"
    write_grid(ws, master_cols, top)

    build_dashboard(wb, all_rows)

    for idx, (slug, rows) in enumerate(tabs, start=4):
        name = f"{idx:02d}_{slug}"[:31]
        ws = wb.create_sheet(name)
        write_grid(ws, schema, rows)

    wb.save(OUT)

    print(f"Wrote {OUT}")
    print(f"  tabs merged : {len(tabs)}")
    print(f"  total rows  : {len(all_rows)}")
    print(f"  top targets : {len(top)} (fit >= 8)")
    print(f"  duplicates  : {sum(1 for r in all_rows if r.get('Duplicate_Of'))}")
    for p in problems:
        print(f"  WARNING: {p}")
    return 0


def _score(r):
    try:
        return int(float(r.get("Fit_Score")))
    except (TypeError, ValueError):
        return 0


if __name__ == "__main__":
    sys.exit(main())
