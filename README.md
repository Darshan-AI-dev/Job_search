# Mumbai Finance Job Search

A twelve-agent research swarm that maps finance openings in Mumbai against one specific profile,
and merges the results into a single formatted Excel workbook.

**Deliverable:** `Mumbai_Finance_Jobs_Master.xlsx`

---

## The profile being searched for

Revenue Management / Portfolio Management at **Amherst Holdings** — a US institutional
single-family-rental owner-operator and real estate investment platform. Currently owns revenue
and leasing strategy across a large residential portfolio. Previously ran retail disposition
strategy for homes, and fund/JV capital planning and distribution modelling.

The search targets the **Manager → VP / Director** band (roughly 5–12 years) in **Mumbai and the
Mumbai Metropolitan Region only**.

Three threads run through the whole workbook, because they are the three most portable pieces of
that background:

- **Pricing and yield** — rent optimisation is revenue management, and revenue management is a job
  title in hospitality, aviation, e-commerce and co-living.
- **Asset-level exit strategy** — retail disposition of homes at scale is portfolio analytics under
  another name.
- **Fund mechanics** — capital planning, JV structures, waterfalls and distributions are a whole
  job family inside Mumbai's alternatives GCCs, and one very few candidates can speak to fluently.

---

## How it works

```
agents/COMMON_BRIEF.md      shared brief: profile, schema, integrity rules, fit rubric
agents/prompts/A01..A12.md  one lane prompt per agent (job family x portal mix)
config/schema_header.csv    the canonical 21-column contract every agent writes to
data/tabs/*.csv             one CSV per agent — raw research output
scripts/build_workbook.py   validates, merges, de-duplicates, formats
Mumbai_Finance_Jobs_Master.xlsx
```

Each agent owns one lane so the twelve tabs do not collide, and each writes only its own file so
they can run in parallel without contending for the workbook. The merge step is a pure function of
`data/tabs/` — rebuild any time with:

```bash
python3 scripts/build_workbook.py
```

### The twelve lanes

| Agent | Lane | Portal mix |
|---|---|---|
| A01 | Real estate PE, REITs & InvITs — investments and asset management | iimjobs, LinkedIn, company careers, trade press |
| A02 | Fund finance, capital planning, distributions & waterfalls | Naukri, company careers, eFinancialCareers |
| A03 | Revenue management, pricing & yield strategy (cross-industry) | LinkedIn, Naukri, Instahyre, Hirist |
| A04 | FP&A, business finance & corporate finance | Naukri, foundit, Glassdoor, Indeed |
| A05 | Investment banking — real estate, infra, M&A | iimjobs, LinkedIn, company careers |
| A06 | Equity research & buy-side investment analysis | eFinancialCareers, iimjobs, Naukri |
| A07 | Infrastructure, project & structured finance, InvITs | Naukri, LinkedIn, company careers |
| A08 | Global Capability Centres — strategy & business management | LinkedIn, Glassdoor, AmbitionBox |
| A09 | Asset management, portfolio management, wealth & AIF | iimjobs, LinkedIn, Robert Walters |
| A10 | NBFC, housing finance & credit/portfolio analytics | Naukri, foundit, Shine, TimesJobs |
| A11 | Quant, data & decision science in finance and real assets | Instahyre, Hirist, Cutshort, Wellfound |
| A12 | Private credit, family offices & search-firm mandates | Michael Page, Robert Walters, Native, Vahura |

---

## What the data is, and what it is not

**Read this before acting on any row.**

The machine this ran on could reach a web search index, but its network proxy blocked direct
access to Naukri, LinkedIn, Glassdoor, Indeed, iimjobs, eFinancialCareers, Greenhouse and
corporate career domains — all of them return `EGRESS_BLOCKED`. Agents could therefore see what
search returned *about* a role, but could not open the posting to confirm it.

Rather than paper over that, every row carries a `Listing_Status`:

| Status | Meaning |
|---|---|
| `Verified live posting` | Search results showed this specific role at this specific firm, with enough detail to be confident it exists. |
| `Search-surfaced` | Search indicates the firm is hiring for this kind of role in Mumbai; the individual posting was not opened. **Confirm before applying.** |
| `Target employer - not verified` | A well-founded target based on Mumbai presence and hiring pattern. No live-posting evidence. An outreach lead, not a listing. |

Expect the middle and last categories to dominate. That is the honest shape of what this
environment could establish. The workbook is a **prioritised map of where to look and what to say**,
not a verified live feed — every row still needs the posting checked before you spend time on it.

Agents were instructed never to invent job IDs, URLs, recruiter names or salary precision.
`Comp_Basis` marks whether a compensation figure was posted, estimated from market, or unknown.

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
