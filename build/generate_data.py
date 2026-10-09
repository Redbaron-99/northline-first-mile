"""
Synthetic first-mile linehaul data for a fictional Canadian retailer ("Northline Retail").
Jan 2023 to Sep 2026, Mon-Sat operations, 53' trailers holding 26 pallet positions.
Everything here is invented for a portfolio project. Distances are approximate road km.

The history has a deliberate improvement story so year-over-year views have something to show:
  * volume grows about 6% a year, with a Q4 peak (November highest) and a January dip
  * load building improves: trailers are cubed out at ~23 pallets in 2023, ~24.5 in 2024, 26 from 2025
  * Jul 2024: Brampton -> Winnipeg moves its primary carrier from Prairie Haul to TransNorth
  * Jan 2025: Monday appointment slots rebalanced, so the Monday congestion penalty shrinks
  * Apr 2025: six thin lanes drop from daily to Mon/Wed/Fri departures (consolidation)
  * Sep 2025: a Winnipeg -> Brampton vendor backhaul starts, cutting empty return km
  * carrier scorecards lift every carrier's on-time a little each year
Winter (Dec-Mar) hurts long lanes; November-December peak adds congestion.
"""
import json, math, random, datetime as dt

random.seed(20261009)

NODES = {
    # code: (name, province, type, lat, lon)
    "BRA": ("Brampton", "ON", "DC", 43.73, -79.76),
    "LAV": ("Laval", "QC", "DC", 45.57, -73.69),
    "DEL": ("Delta", "BC", "DC", 49.08, -123.06),
    "WPG": ("Winnipeg", "MB", "Cross-dock", 49.90, -97.14),
    "MON": ("Moncton", "NB", "Cross-dock", 46.09, -64.78),
    "CGY": ("Calgary", "AB", "Cross-dock", 51.05, -114.07),
    "OTT": ("Ottawa", "ON", "Service centre", 45.42, -75.70),
    "LDN": ("London", "ON", "Service centre", 42.98, -81.25),
    "SUD": ("Sudbury", "ON", "Service centre", 46.49, -80.99),
    "TBY": ("Thunder Bay", "ON", "Service centre", 48.38, -89.25),
    "QUE": ("Quebec City", "QC", "Service centre", 46.81, -71.21),
    "HFX": ("Halifax", "NS", "Service centre", 44.65, -63.58),
    "REG": ("Regina", "SK", "Service centre", 50.45, -104.62),
    "SAS": ("Saskatoon", "SK", "Service centre", 52.13, -106.67),
    "EDM": ("Edmonton", "AB", "Service centre", 53.55, -113.49),
    "KEL": ("Kelowna", "BC", "Service centre", 49.89, -119.50),
}

# origin, dest, road km (approx), mean pallets/day (2026 level), primary carrier, secondary carrier
LANES = [
    ("BRA", "LAV", 570, 45, "Maple Line Freight", "TransNorth Carriers"),
    ("LAV", "BRA", 570, 19, "Maple Line Freight", "TransNorth Carriers"),
    ("BRA", "OTT", 430, 40, "Lakeshore Logistics", "Maple Line Freight"),
    ("BRA", "LDN", 170, 18, "Lakeshore Logistics", "TransNorth Carriers"),
    ("BRA", "SUD", 380, 9, "TransNorth Carriers", "Lakeshore Logistics"),
    ("BRA", "TBY", 1400, 7, "Prairie Haul", "TransNorth Carriers"),
    ("BRA", "WPG", 2100, 60, "Prairie Haul", "TransNorth Carriers"),
    ("WPG", "BRA", 2100, 16, "TransNorth Carriers", "Prairie Haul"),   # backhaul from Sep 2025
    ("LAV", "QUE", 250, 30, "Maple Line Freight", "Lakeshore Logistics"),
    ("LAV", "OTT", 200, 14, "TransNorth Carriers", "Maple Line Freight"),
    ("LAV", "MON", 1000, 35, "Maple Line Freight", "TransNorth Carriers"),
    ("MON", "HFX", 260, 22, "TransNorth Carriers", "Maple Line Freight"),
    ("WPG", "REG", 570, 15, "Prairie Haul", "Coastal Express"),
    ("WPG", "SAS", 780, 11, "Prairie Haul", "Coastal Express"),
    ("DEL", "KEL", 390, 16, "Coastal Express", "Prairie Haul"),
    ("DEL", "CGY", 970, 48, "Coastal Express", "Prairie Haul"),
    ("CGY", "EDM", 300, 28, "Coastal Express", "Prairie Haul"),
]

# on-time probability at the start of 2023, 2024, 2025, 2026 (scorecard improvement), rate $/km (2023), min charge $
CARRIERS = {
    "Maple Line Freight": ((0.92, 0.93, 0.94, 0.95), 2.30, 620),
    "TransNorth Carriers": ((0.84, 0.86, 0.88, 0.90), 2.07, 570),
    "Lakeshore Logistics": ((0.90, 0.91, 0.92, 0.93), 2.45, 660),
    "Prairie Haul": ((0.76, 0.77, 0.80, 0.85), 1.93, 570),
    "Coastal Express": ((0.88, 0.89, 0.91, 0.92), 2.26, 620),
}
CAP = 26
START = dt.date(2023, 1, 2)    # Monday
END = dt.date(2026, 9, 26)     # Saturday
POOL = {"BRA": 56, "LAV": 26, "DEL": 20}
SEASON = [0.86, 0.88, 0.95, 0.98, 1.00, 1.00, 0.98, 1.04, 1.06, 1.12, 1.24, 1.10]  # Jan..Dec
WEEKDAY = [1.12, 1.0, 0.98, 1.0, 1.05, 0.85]
HOLIDAYS = {(1, 1), (7, 1), (12, 25), (12, 26)}

D_SWITCH = dt.date(2024, 7, 1)      # BRA-WPG primary carrier change
D_MONDAY = dt.date(2025, 1, 6)      # Monday appointment rebalancing
D_CONSOL = dt.date(2025, 4, 7)      # thin lanes to Mon/Wed/Fri
D_BACKHAUL = dt.date(2025, 9, 1)    # WPG -> BRA backhaul starts
THIN = {("BRA", "SUD"), ("BRA", "TBY"), ("LAV", "OTT"), ("WPG", "SAS"), ("WPG", "REG"), ("DEL", "KEL")}


def yrs(day):
    return (day - START).days / 365.25


def interp(vals, t):
    """piecewise-linear over yearly anchor points t=0,1,2,3, flat after"""
    if t >= len(vals) - 1:
        return vals[-1]
    i = int(t)
    return vals[i] + (vals[i + 1] - vals[i]) * (t - i)


def transit_days(km):
    return max(1, math.ceil(km / 750))


def eff_cap(day):
    # pallets a load planner actually fits before the trailer cubes out
    if day < dt.date(2024, 1, 1):
        return 23
    if day < dt.date(2025, 1, 1):
        return 24.5
    return 26


loads = []
backlog = {}   # consolidated lanes: pallets waiting for the next departure day
day = START
while day <= END:
    wd = day.weekday()
    if wd == 6 or (day.month, day.day) in HOLIDAYS:
        day += dt.timedelta(days=1)
        continue
    t = yrs(day)
    vol = 0.84 * 1.06 ** t
    season = SEASON[day.month - 1]
    winter = day.month in (12, 1, 2, 3)
    peak = day.month in (11, 12)
    fuel = interp((0.24, 0.20, 0.18, 0.17), t) + 0.01 * math.sin(t * 6.3)
    infl = 1.035 ** t
    di = (day - START).days
    for (o, de, km, mean, prim, sec) in LANES:
        if (o, de) == ("WPG", "BRA") and day < D_BACKHAUL:
            continue
        ramp = min(1.0, (day - D_BACKHAUL).days / 90) if (o, de) == ("WPG", "BRA") else 1.0
        demand = max(0, round(random.gauss(mean * vol * season * WEEKDAY[wd] * ramp, mean * 0.22)))
        key = (o, de)
        if key in THIN and day >= D_CONSOL:
            backlog[key] = backlog.get(key, 0) + demand
            if wd not in (0, 2, 4):
                continue
            demand, backlog[key] = backlog[key], 0
        if demand == 0:
            continue
        cap = eff_cap(day)
        n = math.ceil(demand / cap)
        if key == ("BRA", "WPG") and day >= D_SWITCH:
            prim, sec = "TransNorth Carriers", "Prairie Haul"
        base_each = demand // n
        extra = demand - base_each * n
        for i in range(n):
            pallets = min(CAP, base_each + (1 if i < extra else 0)) if n > 1 else demand
            carrier = prim if random.random() < 0.8 else sec
            ot_vals, rate, minc = CARRIERS[carrier]
            p_on = interp(ot_vals, t)
            p_on -= 0.05 if km > 900 else 0.0
            if winter:
                p_on -= 0.06 if km > 900 else 0.02
            if peak:
                p_on -= 0.02
            if wd == 0:
                p_on -= 0.03 if day < D_MONDAY else 0.01
            on = random.random() < p_on
            delay_h = round(random.uniform(-1.5, 1.0), 1) if on else round(random.uniform(2, 20 if km > 900 else 9), 1)
            linehaul = max(minc, rate * km) * infl
            if key == ("WPG", "BRA"):
                linehaul *= 0.62     # backhaul pricing
            cost = round(linehaul * (1 + fuel) * random.uniform(0.97, 1.04))
            loads.append((di, o, de, carrier, pallets, cost, delay_h, 1 if on else 0))
    day += dt.timedelta(days=1)

lane_idx = {(o, d): i for i, (o, d, *_r) in enumerate(LANES)}
car_list = list(CARRIERS)
lanes_out = [{"o": o, "t": de, "km": km, "transit": transit_days(km), "prim": prim, "sec": sec, "mean": mean}
             for (o, de, km, mean, prim, sec) in LANES]
nodes_out = {k: {"name": v[0], "prov": v[1], "type": v[2], "lat": v[3], "lon": v[4]} for k, v in NODES.items()}
carriers_out = {k: {"rate": v[1], "min": v[2]} for k, v in CARRIERS.items()}

# compact encoding: [day offset from start, lane index, carrier index, pallets, cost $, hours late x10, on-time]
rows = [[di, lane_idx[(o, de)], car_list.index(c), p, cost, int(round(late * 10)), on] for (di, o, de, c, p, cost, late, on) in loads]
data = {"meta": {"start": START.isoformat(), "end": END.isoformat(), "cap": CAP, "pool": POOL,
                 "company": "Northline Retail (fictional)", "carriers": car_list,
                 "fields": ["day", "lane", "carrier", "pallets", "cost", "late_x10", "on_time"]},
        "nodes": nodes_out, "lanes": lanes_out, "carriers": carriers_out, "loads": rows}
json.dump(data, open("data.json", "w"), separators=(",", ":"))

# ---- also write sample CSVs for the repo ----
import csv, os
os.makedirs("../data", exist_ok=True)
km_of = {(o, d): km for (o, d, km, *_r) in LANES}
with open("../data/sample_loads.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["date", "origin", "destination", "carrier", "pallets", "cost", "on_time", "hours_late", "km"])
    for (di, o, de, c, p, cost, late, on) in loads:
        w.writerow([(START + dt.timedelta(days=di)).isoformat(), o, de, c, p, cost, "Y" if on else "N", late, km_of[(o, de)]])
with open("../data/sample_sites.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["code", "name", "type", "lat", "lon", "trailer_pool"])
    for k, v in NODES.items():
        w.writerow([k, v[0], v[2], v[3], v[4], POOL.get(k, "")])

# ---- summary for checking ----
print("loads", len(loads), "json KB", round(len(json.dumps(data, separators=(",", ":"))) / 1024))
by_year = {}
for L in loads:
    y = (START + dt.timedelta(days=L[0])).year
    by_year.setdefault(y, []).append(L)
for y, Ls in sorted(by_year.items()):
    n = len(Ls); pal = sum(l[4] for l in Ls); cost = sum(l[5] for l in Ls)
    print(y, "loads", n, "otp", round(sum(l[7] for l in Ls) / n, 3), "fill", round(pal / (n * CAP), 3),
          "cpl", round(cost / n), "cpp", round(cost / pal, 2))
