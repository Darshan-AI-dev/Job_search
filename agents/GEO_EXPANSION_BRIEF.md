# GEOGRAPHY EXPANSION BRIEF — Gulf, Singapore & India beyond Mumbai

Read this **together with** `/home/user/Job_search/agents/COMMON_BRIEF.md`. That file still governs
the candidate profile, the CSV contract, the `Listing_Status` integrity rules and the fit rubric.
This file **replaces its geography section only**, and adds two columns.

---

## 1. What changed

The original search was Mumbai-only, and agents correctly dropped good rows on that rule —
airline and travel revenue management in Gurugram, fund administration in Pune and Hyderabad,
analytics centres in Pune and Bengaluru. Those are now in scope. The candidate is open to:

- **UAE (Dubai, Abu Dhabi)** and **Qatar (Doha)**
- **Singapore**
- **Other major Indian cities**, for a genuinely better opportunity than Mumbai offers

Mumbai is already covered by twelve existing tabs. **Do not re-cover Mumbai.** If a firm's role
is Mumbai-based, leave it out — it belongs to another agent's tab.

---

## 2. Two new columns

The schema now carries `Country` and `City` immediately before `Location_Micro_Market`.

- `Country` — `UAE`, `Qatar`, `Singapore`, `India`, `Saudi Arabia`.
- `City` — `Dubai`, `Abu Dhabi`, `Doha`, `Singapore`, `Bengaluru`, `Gurugram`, `Noida`,
  `Hyderabad`, `Pune`, `Chennai`, etc.
- `Location_Micro_Market` — the district or free zone: `DIFC`, `ADGM`, `Downtown Dubai`,
  `Business Bay`, `Dubai Hills`, `Al Maryah Island`, `West Bay`, `Lusail`, `Marina Bay`,
  `Raffles Place`, `Whitefield`, `ORR`, `Cyber City`, `Golf Course Road`, `HITEC City`,
  `Kharadi`, or `<City> (unspecified)`.

---

## 3. Visa reality — weight your fit scores by this

This is researched, not assumed. It should change how you score, and it belongs in
`Application_Notes` wherever it bites.

**UAE — genuinely low friction.** Work permits are employer-sponsored through MOHRE, and as of
2026 AI-assisted processing has cut employment-visa timelines to roughly 7–10 working days for
a complete employer-sponsored application. Standard work visas run two years. There is also a
self-sponsored **Green Visa** (5 years) for skilled professionals earning AED 15,000+/month, and
a 10-year **Golden Visa** on nomination or salary-based routes. No points test. Income tax is nil.

**Qatar — low friction, employer-led.** Employer-sponsored work permit, then medical, biometrics
and a QID residence permit on arrival. Straightforward, but the market is far smaller and more
state-linked than the UAE. Income tax is nil.

**Singapore — NOT low friction. Do not treat it as equivalent.** An Employment Pass in
**financial services** requires a minimum qualifying salary of **SGD 6,200/month**, rising with age
to **SGD 11,800/month at 45 and above** — and on top of that the role must clear **40 points on the
COMPASS framework**, which scores salary against local PMET benchmarks, qualifications, workforce
diversity and local employment share. Only candidates at SGD 22,500+/month are exempt from COMPASS.
From **1 January 2027** the financial-services floor rises again to SGD 6,600. The practical effect
is that Singapore employers sponsor mid-career foreign hires more reluctantly than Gulf employers.
**Score Singapore rows one point lower than an identical Gulf role** unless the employer is a large
institution with a known track record of sponsoring, and say why in `Application_Notes`.

**India (non-Mumbai) — no visa question at all.** The trade is city and sector, not paperwork.

---

## 4. Compensation — do not reuse the Mumbai bands

`data/reference/comp_benchmarks.csv` is **Mumbai-specific**. Do not apply it abroad.

- Report Gulf pay in **AED/month or AED/year** where that is how the market quotes it, or in
  **INR LPA equivalent** — but say which in `Comp_Basis` (e.g. `Market estimate (AED)`).
- Report Singapore pay in **SGD/month or SGD/year**, same rule.
- Remember the tax difference is part of the offer: UAE and Qatar levy **no personal income tax**,
  Singapore is progressive, India is not. A headline number is not comparable across these
  markets and you should not pretend it is.
- If you genuinely do not know the local band, write `Not disclosed` with `Comp_Basis` = `Unknown`.
  That is a better answer than a confident wrong number.

---

## 5. Everything else is unchanged

Same 40–50 rows, same `csv.DictWriter` requirement, same header match against
`/home/user/Job_search/config/schema_header.csv` (now 26 columns), same strict `Listing_Status`
discipline, same fit rubric, same ban on invented job IDs, URLs, recruiter names and salary
precision.

**Write your file early.** Build a complete honest file first from what you know, then spend your
search budget upgrading rows. Two earlier runs were killed by rate limits before writing, and the
work was lost.
