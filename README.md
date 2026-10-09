# Northline First Mile

An interactive first-mile linehaul control tower for a fictional Canadian retailer.

**Live app:** 

https://redbaron-99.github.io/northline-first-mile/

Northline Retail moves freight from 3 DCs (Brampton, Laval, Delta) to cross-docks and service centres across Canada: 17 lanes, 5 carriers, about 27,000 loads from January 2023 to September 2026. All data is synthetic, with a built-in improvement story so the year-over-year views have something to show.

## What the app does

| View | Question it answers |
|---|---|
| Filters | View by week, month, quarter or year; pick a from/to period, step back and forward, or use Latest 12 months / Last full year / All history. Every KPI compares with the same period one year earlier |
| KPIs | Hover (or tap) any KPI for what it means, the logic, the formula and the numbers behind it |
| Network | Map coloured by on-time %, line width by volume, click a lane for carrier detail. Trend chart over the full history, same-month-each-year chart and a year-over-year table |
| Lanes & carriers | Sortable lane and carrier scorecards with change vs last year |
| Consolidation | How many departures per week should each lane run? Planned from the selected period |
| Peak planner | How many trailers and how much spot freight does a +30% peak need? |
| Trailer balance | How many trailer-km run empty, and which return lane is worth finding freight for? |

## Findings on the sample data

- On-time rose from 82.8% in 2023 to 87.4% in the latest 12 months, still short of the 92% target. Prairie Haul went from 71.5% to 81.3% and its share fell from 24% to 14% after Brampton to Winnipeg moved to another carrier.
- Trailer fill rose from 59% to 74%, mostly from moving six thin lanes to three departures a week in April 2025. Cost per pallet fell from $128.88 to $114.92 even though cost per load rose with rates and inflation.
- On the 2023 base, the consolidation model finds $2.8M a year of savings. On the latest 12 months it finds $1.1M: the rest has already been captured.
- Empty trailer-km fell from 48% to 42% after a Winnipeg to Brampton backhaul started in September 2025.

## Use your own data

Open the **Your data** tab in the app and load two CSV files. They are read in your browser only; nothing is uploaded.

**Loads file** (one row per load)

| Column | Required | Example |
|---|---|---|
| date | Yes | 2026-07-06 (more than a year of history unlocks the year-over-year views) |
| origin | Yes | BRA (a code from the sites file) |
| destination | Yes | OTT |
| carrier | Yes | Lakeshore Logistics |
| pallets | Yes | 24 |
| cost | Yes | 1310.50 (total $ incl. fuel) |
| on_time | Yes* | Y or N (*optional if hours_late is given) |
| hours_late | No | 3.2 (late = more than 1 hour) |
| km | No | 430 (else estimated from coordinates) |

**Sites file** (one row per site): `code, name, type (DC / Cross-dock / Service centre), lat, lon, trailer_pool (optional)`

Starter files are in `data/`: blank templates plus the full sample data as CSV (`sample_loads.csv`, `sample_sites.csv`), so you can see the exact format or edit the sample.

Your loaded data is remembered in your browser for next time. **Back to sample data** clears it.

## How it is built

- `build/generate_data.py` creates the synthetic loads (Python, no dependencies).
- `build/geo.mjs` projects the Canada map to SVG (Node, `npm install`).
- `build/template.html` is the app: plain JavaScript and SVG, no framework. Calculations run in the browser, so sliders update instantly.
- `index.html` is the finished single-file app.

Rebuild: `cd build && npm install && python generate_data.py && node geo.mjs && python build_site.py`

## Limits

- Data is synthetic; carrier names, volumes and costs are invented.
- Consolidation, peak and trailer balance use average weekly volume over the selected period; the max-fill slider is the buffer for day-to-day swings.
- Trailer counts assume DC-origin lanes use the owned pool and cross-dock lanes use carrier equipment.
