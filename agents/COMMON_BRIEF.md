# COMMON BRIEF — Mumbai Finance Job Search Swarm

Every research agent reads this file first, then follows its own agent-specific prompt.

---

## 1. Who we are searching for (the candidate profile)

**Current role:** Revenue Management / Portfolio Management at **Amherst Holdings** (US institutional
single-family-rental owner-operator, asset manager and real estate investment platform).

**What he owns today:** revenue strategy and leasing strategy across a large residential
portfolio — pricing/rent optimisation, occupancy and renewal strategy, revenue forecasting,
portfolio performance management.

**Prior scope inside the same platform:**
- **Retail disposition strategy** for single-family homes (deciding which assets to sell, when,
  into which channel, at what price — asset-level exit strategy at scale).
- **Fund and JV capital planning** — capital deployment plans, commitments, capital calls.
- **Distribution modelling** — waterfall / promote / preferred-return mechanics across funds and
  joint ventures.
- A long tail of ad-hoc strategic and analytical side projects across the platform.

**Implied toolkit:** financial modelling, pricing and yield analytics, scenario/forecast modelling,
fund waterfall mechanics, asset-level investment analysis, SQL/Excel/BI-driven decision support,
and the ability to run cross-functional strategy work.

**Assumed seniority band (state it if a listing falls outside):** roughly **5–12 years** of
experience — in Indian market terms that maps to **Manager / Senior Manager / AVP / VP /
Director / Principal**. Do not fill the sheet with fresh-graduate or pure-entry roles, and do not
fill it with MD / CFO / Partner roles.

**Geography:** **Mumbai / Mumbai Metropolitan Region only** — including BKC, Lower Parel/Worli,
Nariman Point/Fort, Andheri/SEEPZ, Powai, Goregaon, Malad, Thane, Navi Mumbai (Airoli/Vashi/
Belapur). Hybrid roles based in Mumbai count. Pune / Bengaluru / Gurugram / Hyderabad do **not**
count — leave them out entirely.

---

## 2. Hard constraint on this machine — READ THIS BEFORE YOU START

The network egress proxy in this container **blocks WebFetch to essentially every job board and
corporate career site** (Naukri, LinkedIn, Glassdoor, Indeed, iimjobs, foundit, eFinancialCareers,
Greenhouse, Workday, and company career domains all return `EGRESS_BLOCKED`). This has been tested.

**Therefore:**
- Load the search tool first: `ToolSearch` with query `select:WebSearch`, then use **WebSearch**.
- **Do not burn turns on WebFetch against job boards.** One or two probes is fine if you want to
  confirm; after that, stop. WebSearch is your research instrument.
- WebSearch returns result titles, URLs and a synthesised summary. Mine all three. Vary your
  queries aggressively — company names, role titles, portal-specific phrasing, recruiter names,
  hiring-news phrasing. Run **at least 25–35 distinct searches** before you write your file.

Because you cannot open the posting itself, **you must be honest about what each row is.** That is
what the `Listing_Status` column exists for. See §4.

---

## 3. Your output file

Write exactly one CSV to:

    /home/user/Job_search/data/tabs/<YOUR_TAB_SLUG>.csv

- **40–50 data rows** (plus the header row). 45 is the target.
- The header must be **byte-identical** to `/home/user/Job_search/config/schema_header.csv`.
- **Write it with Python's `csv` module**, not by echoing raw text — fields contain commas.
  Build a list of dicts and use `csv.DictWriter`. This is not optional; hand-written CSV will
  corrupt the merge.
- No duplicate `Company` + `Role_Title` pairs inside your own file.
- Before you finish, validate:

```python
import csv
rows = list(csv.DictReader(open(PATH)))
hdr = open('/home/user/Job_search/config/schema_header.csv').read().strip().split(',')
assert list(rows[0].keys()) == hdr, "header mismatch"
assert 40 <= len(rows) <= 50, f"row count {len(rows)}"
assert all(r['Source_URL'].startswith('http') for r in rows), "bad URL"
print("OK", len(rows))
```

---

## 4. Column definitions — follow these exactly

| Column | What goes in it |
|---|---|
| `Listing_ID` | `<YOUR_AGENT_CODE>-001` … ascending, zero-padded to 3. |
| `Role_Title` | The role title as posted, or the standard title the employer uses. |
| `Company` | Real, named employer. Never "a leading bank" or "confidential". If a recruiter listing hides the client, name the **recruiter** and say so in `Application_Notes`. |
| `Company_Type` | One of: `Real Estate PE`, `REIT / InvIT`, `Real Estate Developer`, `Proptech`, `Investment Bank`, `Global Capability Centre`, `Asset Manager`, `NBFC / HFC`, `Bank`, `Private Credit`, `Insurance`, `Consulting`, `Family Office`, `Fintech`, `Corporate`, `Recruiter / Search Firm`. |
| `Location_Micro_Market` | BKC, Lower Parel, Worli, Nariman Point, Fort, Andheri East, Powai, Goregaon, Malad, Thane, Navi Mumbai, or `Mumbai (unspecified)`. |
| `Seniority` | `Analyst`, `Senior Analyst`, `Manager`, `Senior Manager`, `AVP`, `VP`, `Director`, `Principal`, `Associate`. |
| `Experience_Required` | e.g. `5-8 yrs`. If not stated, give the band the role normally carries and note the inference in `Comp_Basis`-style honesty — i.e. write `~6-10 yrs (inferred)`. |
| `Function` | Short bucket, e.g. `FP&A`, `RE Investments`, `Fund Finance`, `Revenue Management`, `Equity Research`, `IB Coverage`, `Credit Risk`, `Strategy`, `Portfolio Management`, `Data & Analytics`. |
| `Key_Skills` | 3–6 semicolon-separated skills the role actually calls for. |
| `Comp_Range_INR_LPA` | e.g. `35-55`. If genuinely unknown write `Not disclosed`. **Never invent a precise number.** |
| `Comp_Basis` | `Posted` (the listing stated it), `Market estimate` (your informed range for that title/firm/level in Mumbai), or `Unknown`. |
| `Portal` | Where you found it — `Naukri`, `LinkedIn`, `iimjobs`, `Glassdoor`, `Indeed`, `foundit`, `Instahyre`, `Hirist`, `eFinancialCareers`, `Company Careers Page`, `Michael Page`, `Robert Walters`, `Native`, `Vahura`, `AmbitionBox`, `Wellfound`, `News / Hiring Signal`, etc. |
| `Source_URL` | **A real URL that appeared in your search results**, or a deterministic portal search-deep-link that will resolve (e.g. `https://www.naukri.com/fund-accounting-jobs-in-mumbai`). Must start with `http`. Never fabricate a posting-ID URL you did not see. |
| `Listing_Status` | **Be strict here — this is the integrity column.** Use exactly one of: `Verified live posting` (the search result itself showed this specific role at this specific company, with enough detail to be confident), `Search-surfaced` (search results indicate this company is hiring for this kind of role in Mumbai, but the individual posting was not seen), `Target employer - not verified` (a well-founded target based on the firm's Mumbai presence and hiring pattern; no live posting evidence). Expect most rows to be the middle or last category — **that is fine and expected. Do not upgrade a row's status to look better.** |
| `Posting_Date` | Only if you actually saw it. Otherwise `Unknown`. |
| `Date_Found` | `2026-09-19`. |
| `Fit_Score` | Integer 1–10, using the rubric in §5. |
| `Fit_Rationale` | One sentence, concrete, tied to *his* background — not generic praise. |
| `Profile_Hook` | Which specific piece of his experience to lead with in the application (e.g. "JV waterfall + distribution modelling", "retail disposition strategy = asset-level exit analytics", "rent/pricing optimisation = yield management"). |
| `Application_Notes` | Practical edge: referral angle, whether it's recruiter-fronted, visa/relocation notes, what to emphasise, what gap to pre-empt (e.g. "no India market experience — lead with platform-level analytics transferability"). |
| `Agent_Source` | `<YOUR_AGENT_CODE>` — same for every row in your file. |

---

## 5. Fit-score rubric (apply consistently — the master sheet sorts on this)

- **9–10** — Direct hit. Revenue management / pricing strategy / portfolio management / asset
  management strategy / fund & JV capital planning / distribution & waterfall modelling, at a real
  estate investment platform, REIT/InvIT, RE PE fund, or a proptech/residential operator.
- **7–8** — Strong adjacency. Real-estate-linked FP&A or strategy; fund finance / capital &
  distributions at an alternatives GCC; RE or infra investment banking or equity research;
  pricing/yield/revenue-management outside real estate (hospitality, airlines, e-commerce,
  subscription); investment strategy at an asset manager.
- **5–6** — Transferable but a step sideways. General corporate FP&A, business finance, or strategy
  at a financial institution or GCC; generalist portfolio analytics.
- **3–4** — Weak. Domain is off (pure accounting, audit, statutory reporting, back-office ops,
  compliance) even if the title sounds finance-y.
- **1–2** — Off-profile. Include only if there is a specific reason worth recording.

Aim for a realistic spread. A file where every row scores 9 is not research, it is flattery —
and it makes the master sheet useless for prioritising.

---

## 6. Quality bar

- **Named, real, Mumbai-present employers.** If you are not confident the firm has a Mumbai office
  doing this function, leave it out.
- **No invented job IDs, no invented recruiter names, no invented salary precision.**
- Prefer **depth over padding**: 42 well-evidenced rows beat 50 with filler.
- Stay inside your own lane (your agent-specific prompt) so the twelve tabs do not collide. Some
  overlap at the edges is unavoidable and fine — the merge step de-duplicates.
- When you finish, reply with: rows written, the `Listing_Status` breakdown (how many of each),
  the `Fit_Score` distribution, and the 5 strongest finds with a one-line reason each.
