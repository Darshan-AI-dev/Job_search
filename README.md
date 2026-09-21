# Finance Careers — Multi-Geography Job Search

A 23-lane research swarm mapping finance roles against one specific profile, across 16 countries,
merged into a single formatted Excel workbook.

**Deliverable:** `Finance_Careers_Master.xlsx` — 1,118 rows, 30 sheets.

---

## The profile being searched for

Revenue Management / Portfolio Management at **Amherst Holdings** — a US institutional
single-family-rental owner-operator and real estate investment platform. Currently owns revenue
and leasing strategy across a large residential portfolio. Previously ran retail disposition
strategy for homes, and fund/JV capital planning and distribution modelling.

Target band: **Manager → VP / Director**, roughly 5–12 years.

Three threads run through every lane, because they are the three most portable pieces of that
background:

- **Pricing and yield** — rent optimisation is revenue management, and revenue management is a job
  title in hospitality, aviation, e-commerce, co-living and flexible workspace.
- **Asset-level exit strategy** — retail disposition of homes at scale is portfolio analytics under
  another name, and it maps onto anything that prices a depreciating asset for resale.
- **Fund mechanics** — capital planning, JV structures, waterfalls and distributions are a whole
  job family, and one very few candidates can speak to fluently.

---

## Geography

The search started Mumbai-only and widened on one rule: **how hard the work visa actually is**.
That rule is researched and documented on the `06_VISA_PATHWAYS` tab, and it changes the scoring —
Singapore rows are marked down a point against an identical Gulf role, because the Employment Pass
is a real constraint rather than a formality.

| Region | Rows | Lanes |
|---|---|---|
| India — Mumbai | 575 | 12 lanes by job family |
| India — other cities | 138 | Bengaluru, Delhi NCR, Hyderabad/Pune/Chennai |
| UAE | 160 | Real estate, sovereign capital, revenue management |
| Singapore | 48 | Real assets |
| Australia / New Zealand | 49 | Real assets, build-to-rent, revenue management |
| Qatar / Saudi Arabia | 53 | Doha primary, Riyadh secondary |
| Europe | 50 | Luxembourg, Dublin, Amsterdam, Frankfurt |
| Africa / Indian Ocean | 45 | Mauritius, South Africa, Kenya, Morocco, Rwanda |

Two Indian lanes exist specifically to recover roles the original Mumbai-only rule forced agents
to discard — airline and travel revenue management in Gurugram, and fund administration in Pune
and Hyderabad.

---

## How it works

```
agents/COMMON_BRIEF.md          shared profile, CSV contract, integrity rules, fit rubric
agents/GEO_EXPANSION_BRIEF.md   replaces the geography rule; carries researched visa facts
agents/prompts/*.md             one prompt per lane
config/schema_header.csv        the canonical 26-column contract
data/tabs/*.csv                 one CSV per lane — raw research output
data/reference/                 compensation benchmarks and visa pathways
scripts/enrich.py               verification pass: corrections, pay benchmarking
scripts/build_workbook.py       validates, merges, de-duplicates, formats
Finance_Careers_Master.xlsx
```

Rebuild any time with:

```bash
python3 scripts/enrich.py && python3 scripts/build_workbook.py
```

---

## Working the workbook

**Start on `02_ACTION_PLAN`.** It is the working shortlist, with blank tracking columns to fill in.

| Priority | Meaning |
|---|---|
| **1 — Apply now** | A verified live posting at fit 8+. Send an application. |
| **2 — Strong, verify first** | A live posting below the top fit band, or a strong role with partial evidence. Confirm it is open before spending time. |
| **3 — Outreach target** | A well-matched employer with no posting seen. The move is a direct approach, not an application. |

Then: `01_MASTER` for everything ranked, `03_TOP_TARGETS` for fit 8+, `04_DASHBOARD` for where
roles cluster, `05_COMP_BENCHMARKS` for what things actually pay, `06_VISA_PATHWAYS` before
committing to any geography.

---

## Second pass: what was verified directly

The twelve agents worked blind to the actual postings. A follow-up research pass checked the
highest-value rows and wrote its findings into three added columns.

| Column | What it holds |
|---|---|
| `Comp_Check` | The row's pay estimate scored against `data/reference/comp_benchmarks.csv` — `In line`, `Above benchmark`, `Below benchmark`, or `Not benchmarked`. |
| `Verification_Note` | What was checked and what was found, including corrections and downgrades. Blank means the row is still unverified agent work. |
| `Last_Verified` | Date of the check. |

**Compensation was the largest systematic gap.** Every agent estimate came from priors, not data.
Benchmarked against sourced Mumbai market bands, roughly a quarter of rows sit above market.
Each benchmark carries its own `Confidence` rating — an `Above benchmark` flag scored against a
`Low` confidence band is a hint, not a verdict. One band (fund finance) was revised upward during
this pass after the first version proved to be built on junior-skewed data.

**Corrections applied**, from registered-office and company records:

| Employer | Correction |
|---|---|
| Blackstone India | BKC → **Nariman Point** (Express Towers). This was the top-ranked row in the workbook. |
| HDFC Capital Advisors | Nariman Point / Lower Parel → **Churchgate** (Ramon House). Both prior values were wrong. |
| Nexus Select Trust | → **Vikhroli** (Embassy 247, the manager's office). |
| NIIF | unspecified → **BKC** (UTI Tower). |
| KKR India | unspecified → **Worli** (Altimus). |
| IndiGrid | unspecified → **Kalina, Santacruz East** (Windsor). |
| Godrej Fund Management | confirmed **Vikhroli** (Godrej One). |
| Brookfield India REIT | confirmed **BKC** (Godrej BKC) — its Mumbai *assets* are in Powai, the corporate seat is not. |

**One upgrade:** Welspun One's Asset Management role (8–10 yrs) was found as a live posting on
foundit, with a posted scope close to the candidate's current remit.

**One downgrade:** Stanza Living fell from fit 9 to 6. The portfolio-level revenue and occupancy
seat the row assumed does not appear to exist — the company's visible Mumbai hiring is Cluster
Manager (Property Operations) and Sales Manager, which are property-level execution roles.

Several rows also gained negative findings worth having: no open roles surfaced at Nexus Select
Trust, Knowledge Realty Trust or Godrej Fund Management, and HDFC Capital's visible hiring was
internships. Those stay as outreach targets rather than being quietly presented as openings.

## Working the workbook

1. **`02_TOP_TARGETS`** — fit 8+. Sort by `Listing_Status` and work `Verified live posting` first.
2. **`Profile_Hook`** tells you which piece of the background to lead with; **`Application_Notes`**
   gives the angle, the gap to pre-empt, or the recruiter to approach.
3. **`01_MASTER`** — everything, ranked. Filter `Duplicate_Of` to blank to hide cross-tab repeats.
4. **`03_DASHBOARD`** — where the openings actually cluster by sector, function and channel.
5. **Tab 12 is an outreach map**, not just a job list. Mumbai's senior alternatives and private
   credit seats move through search firms rather than job boards.

## Re-running a lane

Any lane can be refreshed on its own without touching the others — hand its prompt file to a fresh
agent, let it overwrite its CSV, then rebuild:

```bash
# e.g. refresh the real estate PE lane, then:
python3 scripts/build_workbook.py
```
