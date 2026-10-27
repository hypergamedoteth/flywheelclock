#!/usr/bin/env python3
"""Regenerate data/oil.json. Free official data only: OPEC Annual Statistical Bulletin 2026 (reserves, trade),
EIA open data API v2 (production, consumption, spot prices, SPR), Natural Resources Canada (oil sands).
Raw pulls live outside the repo (/workspace/fwc-raw: prod24, cons24, crude24, price_a, price_m, spr_all .json, asb26.txt).
Re-run: python3 tools/seed_oil.py && python3 build.py"""
import json, os, re
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("FWC_RAW", "/workspace/fwc-raw")
def J(f): return json.load(open(f"{RAW}/{f}.json"))["response"]["data"]
def fl(v):
    try: return float(v)
    except Exception: return None

src = {
 "asb": ["OPEC Annual Statistical Bulletin 2026 (61st edition): Table 3.1 world proven crude oil reserves, Table 5.2 crude exports, Table 5.6 crude imports", "https://publications.opec.org/asb"],
 "eia_intl": ["U.S. Energy Information Administration, International Energy Statistics (open data API v2): 2024 production and consumption of petroleum and other liquids, and crude oil incl. lease condensate", "https://www.eia.gov/international/data/world"],
 "eia_price": ["EIA spot prices: Cushing OK WTI and Europe Brent, annual and monthly averages (through Sep 2026)", "https://www.eia.gov/dnav/pet/pet_pri_spt_s1_m.htm"],
 "eia_spr": ["EIA weekly U.S. ending stocks of crude oil in the Strategic Petroleum Reserve (WCSSTUS1), through the week of Oct 16, 2026", "https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?n=PET&s=WCSSTUS1&f=W"],
 "nrcan": ["Natural Resources Canada: Oil Resources (171.0 billion barrels proven; 166.3 billion in Alberta's oil sands, 4.7 billion conventional, offshore and tight)", "https://natural-resources.canada.ca/energy-sources/fossil-fuels/oil-resources"],
 "eia_api": ["EIA Open Data API v2 documentation", "https://www.eia.gov/opendata/"],
}

# ---- OPEC ASB Table 3.1 (million barrels, 2025) and 2024 for the change column
R = {"Venezuela": 303701, "Saudi Arabia": 267200, "Iran": 208600, "Iraq": 140000, "United Arab Emirates": 120000, "Kuwait": 101500,
     "Russia": 80000, "Libya": 48363, "United States": 41909, "Nigeria": 37010, "China": 34472, "Kazakhstan": 30000, "Qatar": 25244,
     "Brazil": 16841, "Algeria": 12200, "Norway": 5919, "Canada (conventional, as in OPEC's table)": 5080}
WORLD_R, OPEC_R = 1572459, 1243485
NRCAN_SANDS = 166300
other_r = WORLD_R - sum(R.values())

# ---- OPEC ASB 2025 crude trade (thousand b/d)
EXP = {"Saudi Arabia": 6432, "Russia": 4538, "United States": 3987, "Canada": 3668, "Iraq": 3258, "United Arab Emirates": 2878, "Brazil": 2061,
       "Norway": 1721, "Iran": 1666, "Kazakhstan": 1522, "Nigeria": 1396, "Kuwait": 1329, "Libya": 1212}
EXP_W = 44547
IMP = {"China": 11612, "United States": 6169, "India": 4986, "South Korea": 2784, "Japan": 2407, "Germany": 1608, "Spain": 1240,
       "Italy": 1105, "Netherlands": 1059, "Thailand": 965, "France": 919, "Singapore": 881, "United Kingdom": 808}
IMP_W = 46388

# ---- EIA 2024 production / consumption (thousand b/d)
def table(f):
    d = J(f); rows = {r["countryRegionName"]: fl(r["value"]) for r in d if r["countryRegionTypeName"] == "Country" and fl(r["value"]) is not None}
    w = next(fl(r["value"]) for r in d if r["countryRegionName"] == "World"); return rows, w
prod, prod_w = table("prod24"); cons, cons_w = table("cons24"); crude, crude_w = table("crude24")
topp = sorted(prod, key=lambda k: -prod[k])[:12]; topc = sorted(cons, key=lambda k: -cons[k])[:12]
both = sorted(set(sorted(prod, key=lambda k: -prod[k])[:10]) | set(sorted(cons, key=lambda k: -cons[k])[:10]), key=lambda k: -prod[k])
bpd = lambda k: round(k * 1000)

# ---- EIA prices
pa = {(r["period"], r["product-name"]): float(r["value"]) for r in J("price_a")}
pm = {(r["period"], r["product-name"]): float(r["value"]) for r in J("price_m")}
W_, B_ = "WTI Crude Oil", "UK Brent Crude Oil"
years = [str(y) for y in range(2015, 2026)]

# ---- EIA SPR
spr = sorted(J("spr_all"), key=lambda r: r["period"]); spr = [(r["period"], float(r["value"])) for r in spr]
last_d, last_v = spr[-1]
peak_d, peak_v = max(spr, key=lambda x: x[1])
first_d, first_v = spr[0]
low_since = next(d for d, v in reversed(spr[:-1]) if v <= last_v)  # last earlier week at or below today's level
def year_end(y):
    xs = [x for x in spr if x[0].startswith(str(y))]; return xs[-1] if xs else None
ye = {y: year_end(y) for y in (1990, 2000, 2005, 2010, 2015, 2020, 2021, 2022, 2023, 2024, 2025)}
def mb(v): return f"{v / 1000:,.1f}M"

bps = prod_w * 1000 / 86400
brent25 = pa[("2025", B_)]
sec = []
sec.append({"id": "ticker", "title": "Oil, live", "blocks": [{"type": "ticker", "period_seconds": 86400, "period_label": "a day",
  "label": "projected from EIA's 2024 world average per day",
  "counters": [{"id": "p", "label": "Oil produced worldwide", "annual": prod_w * 1000, "unit": "bbl", "hero": True},
               {"id": "c", "label": "Oil consumed worldwide", "annual": cons_w * 1000, "unit": "bbl"},
               {"id": "v", "label": f"Value of that production at the 2025 average Brent spot price (${brent25:.2f}/bbl)", "annual": prod_w * 1000 * brent25, "unit": "usd"}],
  "note": f"EIA's 2024 world production of petroleum and other liquids was {prod_w:,.0f} thousand barrels a day, so about {bps:,.0f} barrels a second ({prod_w * 1000:,.0f} ÷ 86,400). Consumption was {cons_w:,.0f} thousand a day. \"Petroleum and other liquids\" includes crude oil, natural gas liquids, biofuels and refinery gain, so it is larger than crude oil alone ({crude_w:,.0f} thousand a day). The counters are a 2024 daily average projected forward, not live production. The dollar line uses the 2025 average Brent spot price, not a live price. [[eia_intl]] [[eia_price]]",
  "facts": [["Produced in 2024", f"{prod_w / 1000:,.1f}M bbl/d"], ["Consumed in 2024", f"{cons_w / 1000:,.1f}M bbl/d"], ["Proved reserves (2025)", f"{WORLD_R / 1000:,.1f}B bbl"], ["US SPR, Oct 16 2026", f"{last_v / 1000:,.1f}M bbl"]]}]})

wf_items = [{"label": k, "value": v / 1000, "src": ["asb"]} for k, v in [("Venezuela", R["Venezuela"]), ("Saudi Arabia", R["Saudi Arabia"])]]
wf_items.append({"label": "Canada oil sands (NRCan, not in OPEC's table)", "value": NRCAN_SANDS / 1000, "est": True, "est_label": "other source", "src": ["nrcan"]})
wf_items += [{"label": k, "value": R[k] / 1000, "src": ["asb"]} for k in ("Iran", "Iraq", "United Arab Emirates", "Kuwait", "Russia")]
rest = WORLD_R - sum(R[k] for k in ("Venezuela", "Saudi Arabia", "Iran", "Iraq", "United Arab Emirates", "Kuwait", "Russia"))
wf_items.append({"label": "All other countries (OPEC's world total less the seven above)", "value": rest / 1000, "color": "#3a4252", "src": ["asb"]})
sec.append({"id": "holders", "title": "Who holds the reserves", "lede": f"Proved reserves are oil that is known to exist and can be recovered under current technology and prices. OPEC's 2026 bulletin counts {WORLD_R / 1000:,.1f} billion barrels worldwide at the end of 2025. Here is who holds them, one square per 10 billion barrels.",
  "blocks": [{"type": "waffle", "title": "Proved crude oil reserves by holder, end of 2025", "unit": "billion barrels", "dec": 1, "cell": 10, "cell_label": "10 billion barrels (10,000 million)", "cols": 25,
    "items": wf_items, "total_label": "Total shown (OPEC world total + Canada oil sands)",
    "note": f"The seven named countries hold {(sum(R[k] for k in ('Venezuela','Saudi Arabia','Iran','Iraq','United Arab Emirates','Kuwait','Russia'))) / 1000:,.1f} billion barrels (OPEC ASB Table 3.1). OPEC's table counts Canada's conventional oil ({R['Canada (conventional, as in OPEC' + chr(39) + 's table)'] / 1000:.1f} billion) but leaves out its oil sands. Natural Resources Canada puts oil-sands reserves at 166.3 billion barrels, so that block is added from NRCan and hatched because it is from a different source and basis. Shares are of the combined total (derived). Reserve figures are estimates by nature and get revised. [[asb]] [[nrcan]]"}]})

res_items = [[k.replace(" (conventional, as in OPEC's table)", " (conventional)"), v * 1e6] for k, v in R.items()] + [["All other countries", other_r * 1e6]]
sec.append({"id": "reserves", "title": "Proved reserves by country", "blocks": [
  {"type": "bars", "title": "Proved crude oil reserves, end of 2025 (barrels)", "unit": "bbl", "src": ["asb"], "items": res_items,
   "note": f"OPEC ASB 2026, Table 3.1. World total {WORLD_R:,} million barrels, of which OPEC members hold {OPEC_R:,} ({OPEC_R / WORLD_R * 100:.1f}%, derived). \"All other countries\" = {other_r:,} million (world total less the listed countries). Canada's oil sands (166.3 billion barrels per NRCan) are not in OPEC's table. China's figure rose from 28,182 to 34,472 million barrels in the 2025 edition. [[asb]] [[nrcan]]"},
  {"type": "stats", "items": [["World proved reserves", f"{WORLD_R / 1000:,.1f}B bbl", "OPEC ASB 2026, end of 2025 [[asb]]"], ["OPEC members", f"{OPEC_R / WORLD_R * 100:.1f}%", f"{OPEC_R:,} of {WORLD_R:,} million barrels (derived) [[asb]]"],
     ["Canada, all oil", "171.0B bbl", "166.3B oil sands + 4.7B other, per NRCan [[nrcan]]"], ["United States", f"{R['United States'] / 1000:,.1f}B bbl", "OPEC ASB 2026 [[asb]]"]]}]})

def pr(k): return [k, f"{prod[k] * 1000:,.0f}", f"{crude.get(k, 0) * 1000:,.0f}", f"{cons.get(k, 0) * 1000:,.0f}", f"{(prod[k] - cons.get(k, 0)) * 1000:+,.0f}"]
sec.append({"id": "producers", "title": "Who produces it, who burns it", "lede": f"The world made {prod_w / 1000:,.1f} million barrels a day in 2024 and used {cons_w / 1000:,.1f} million. Figures are EIA's \"petroleum and other liquids\", which includes natural gas liquids and biofuels. [[eia_intl]]",
  "blocks": [
   {"type": "bars", "title": "Production, 2024 (barrels per day)", "unit": "bpd", "src": ["eia_intl"], "items": [[k, bpd(prod[k])] for k in topp]},
   {"type": "bars", "title": "Consumption, 2024 (barrels per day)", "unit": "bpd", "src": ["eia_intl"], "items": [[k, bpd(cons[k])] for k in topc]},
   {"type": "table", "title": "Producers and consumers side by side, 2024 (barrels per day)", "cols": ["Country", "All liquids produced", "Crude oil incl. lease condensate", "Consumed", "Produced − consumed"], "align": "lrrrr",
    "rows": [pr(k) for k in both], "src": ["eia_intl"],
    "note": "The last column is derived (produced minus consumed); a negative number means the country uses more than it makes. EIA reports 2025 consumption for OECD countries only, so 2024 is the latest year with every country. [[eia_intl]]"}]})

sec.append({"id": "trade", "title": "Who sells it, who buys it", "lede": "Crude oil only, 2025, from OPEC's bulletin. Exports and imports differ slightly because of reporting gaps. [[asb]]",
  "blocks": [
   {"type": "bars", "title": "Crude oil exports, 2025 (barrels per day)", "unit": "bpd", "src": ["asb"], "items": [[k, v * 1000] for k, v in EXP.items()],
    "note": f"World crude exports {EXP_W:,} thousand barrels a day. The listed 13 countries are {sum(EXP.values()) / EXP_W * 100:.0f}% of that (derived). OPEC ASB Table 5.2. [[asb]]"},
   {"type": "bars", "title": "Crude oil imports, 2025 (barrels per day)", "unit": "bpd", "src": ["asb"], "items": [[k, v * 1000] for k, v in IMP.items()],
    "note": f"World crude imports {IMP_W:,} thousand barrels a day; China alone is {IMP['China'] / IMP_W * 100:.0f}% (derived). OPEC ASB Table 5.6. [[asb]]"}]})

def pavg(y, n): return f"${pa[(y, n)]:,.2f}"
sec.append({"id": "prices", "title": "How it trades", "lede": "Spot prices are what a barrel sold for on the day, free from the EIA. These are history, not a forecast. [[eia_price]]",
  "blocks": [
   {"type": "stats", "items": [["WTI, Sep 2026 average", f"${pm[('2026-09', W_)]:,.2f}", f"Aug 2026: ${pm[('2026-08', W_)]:,.2f} · Jul 2026: ${pm[('2026-07', W_)]:,.2f} [[eia_price]]"],
                                ["Brent, Sep 2026 average", f"${pm[('2026-09', B_)]:,.2f}", f"Aug 2026: ${pm[('2026-08', B_)]:,.2f} · Jul 2026: ${pm[('2026-07', B_)]:,.2f} [[eia_price]]"],
                                ["Brent minus WTI, Sep 2026", f"${pm[('2026-09', B_)] - pm[('2026-09', W_)]:,.2f}", "Derived from the two averages above [[eia_price]]"]]},
   {"type": "table", "title": "Annual average spot price, US$ per barrel", "cols": ["Year", "WTI (Cushing, OK)", "Brent (Europe)"], "align": "lrr",
    "rows": [[y, pavg(y, W_), pavg(y, B_)] for y in reversed(years)], "src": ["eia_price"],
    "note": "EIA spot price FOB, annual averages. WTI is the US benchmark; Brent is the international one. [[eia_price]]"}]})

sec.append({"id": "spr", "title": "US Strategic Petroleum Reserve", "lede": f"The US government stores crude oil in underground salt caverns on the Gulf Coast. On the week of {last_d} it held {mb(last_v)} barrels. [[eia_spr]]",
  "blocks": [
   {"type": "stats", "items": [["SPR crude oil stocks", f"{mb(last_v)} bbl", f"Week of {last_d} [[eia_spr]]"], ["Peak in EIA's weekly series", f"{mb(peak_v)} bbl", f"Week of {peak_d} [[eia_spr]]"],
                                ["Down from the peak", f"{(peak_v - last_v) / 1000:,.1f}M bbl", f"{(peak_v - last_v) / peak_v * 100:.0f}% (derived) [[eia_spr]]"]]},
   {"type": "table", "title": "SPR stocks at the last weekly reading of each year (million barrels)", "cols": ["Year", "Stocks", "Week"], "align": "lrl",
    "rows": [[str(y), mb(v[1]), v[0]] for y, v in ye.items() if v] + [["Latest", mb(last_v), last_d]], "src": ["eia_spr"],
    "note": f"EIA weekly ending stocks of crude oil in the SPR. The series starts {first_d} at {mb(first_v)}. The last earlier week with stocks at or below today's level was {low_since}, so this is the lowest level since then (derived from the series). [[eia_spr]]"}]})

tl = [
 {"date": first_d[:7], "text": f"EIA's SPR series begins at {mb(first_v)} barrels.", "where": "US Gulf Coast salt caverns", "src": ["eia_spr"]},
 {"date": peak_d[:7], "text": f"SPR stocks reach {mb(peak_v)} barrels, the peak of EIA's weekly series.", "src": ["eia_spr"]},
 {"date": "2020", "text": f"WTI averages ${pa[('2020', W_)]:,.2f} a barrel and Brent ${pa[('2020', B_)]:,.2f}, the lowest annual averages in the 2015 to 2025 table.", "src": ["eia_price"]},
 {"date": "2022", "text": f"Brent averages ${pa[('2022', B_)]:,.2f} a barrel, the highest annual average in the 2015 to 2025 table.", "src": ["eia_price"]},
 {"date": "2024", "text": f"The United States produces {prod['United States'] / 1000:,.1f} million barrels a day of petroleum and other liquids, the most of any country, ahead of Saudi Arabia ({prod['Saudi Arabia'] / 1000:,.1f}M) and Russia ({prod['Russia'] / 1000:,.1f}M).", "src": ["eia_intl"]},
 {"date": "2025", "text": f"OPEC counts {WORLD_R / 1000:,.1f} billion barrels of proved crude oil reserves worldwide; Venezuela ({R['Venezuela'] / 1000:,.1f}B) and Saudi Arabia ({R['Saudi Arabia'] / 1000:,.1f}B) hold the most.", "src": ["asb"]},
 {"date": last_d[:7], "text": f"SPR stocks stand at {mb(last_v)} barrels.", "src": ["eia_spr"]},
]
sec.append({"id": "timeline", "title": "Timeline", "lede": "Milestones from the official series on this page.", "blocks": [{"type": "timeline", "items": sorted(tl, key=lambda x: x["date"])}]})

e = {"type": "commodity", "template": "oil", "slug": "oil", "order": 20, "live": True, "name": "Oil", "symbol": "bbl",
 "title": "Where all the oil is: reserves by country, who produces it, who buys it",
 "description": f"The world holds about {WORLD_R / 1000:,.0f} billion barrels of proved crude oil reserves. See who has them, who produces and consumes the most, the US Strategic Petroleum Reserve and oil prices, from OPEC and EIA data.",
 "tagline": f"About {WORLD_R / 1000:,.0f} billion barrels of proved reserves, and about {bps:,.0f} barrels pumped every second.",
 "card_stat": {"label": "Produced per second", "value": f"~{bps:,.0f} bbl", "note": "EIA 2024 world average"},
 "as_of": "OPEC ASB 2026 (end-2025 reserves), EIA 2024 production, prices to Sep 2026, SPR to Oct 16, 2026",
 "sources": src, "sections": sec}
json.dump(e, open(f"{HERE}/data/oil.json", "w"), indent=1, ensure_ascii=False)
print("oil ok", other_r, last_d, low_since, peak_d)
