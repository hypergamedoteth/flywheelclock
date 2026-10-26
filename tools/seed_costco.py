"""Regenerate data/costco.json from the research files in /workspace/ventures/moneyflow.
Every figure here is copied from costco-fy2026.md, costco-revenue-geography.md,
costco_state_revenue_estimate.csv or timeline-costco.md. Derived values say so.
Re-run:  python3 tools/seed_costco.py && python3 build.py"""
import csv, json, os
R = '/workspace/ventures/moneyflow'
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

src = {
 "10k": ["Costco Wholesale Corp., Form 10-K for the 52 weeks ended Aug 30, 2026 (filed Oct 7, 2026)", "https://www.sec.gov/Archives/edgar/data/909832/000090983226000093/cost-20260830.htm"],
 "markup": ["Costco Canada customer service: markup policy", "https://customerservice.costco.ca/app/answers/answer_view/a_id/1017419/"],
 "fortune": ["Fortune: Costco promises the hot dog and drink combo will always be $1.50", "https://fortune.com/article/costco-promises-hot-dog-drink-combo-will-always-be-1-50/"],
 "wsj_hotdog": ["The Wall Street Journal (2022), on Costco's $1.50 hot dog and in-house hot dog production", None],
 "wsj_kirkland": ["The Wall Street Journal, Jul 12, 2025: \"The Pants Cost $20. They Explain $86 Billion of Costco Sales\"", None],
 "cfodive": ["CFO Dive: Costco raises minimum hourly wage (2025 earnings call)", "https://www.cfodive.com/news/costco-raises-minimum-hourly-wage-20-compensation/742075/"],
 "about": ["Costco: About us", "https://www.costco.com/f/-/about"],
 "irfaq": ["Costco Investor Relations: Investor FAQs", "https://investor.costco.com/resources/investor-faqs"],
 "pr": ["Costco press releases (investor.costco.com)", "https://investor.costco.com/"],
 "wiki": ["Wikipedia: Costco (secondary source)", "https://en.wikipedia.org/wiki/Costco"],
 "sn": ["Supermarket News, Oct 9, 1995 (Kirkland Signature launch)", None],
 "wh": ["Costco.com warehouse locations by state (counted Oct 26, 2026)", "https://www.costco.com/warehouse-locations"],
}

# ---- states (estimate) from the research CSV
abbr = dict(Alabama="AL",Alaska="AK",Arizona="AZ",Arkansas="AR",California="CA",Colorado="CO",Connecticut="CT",Delaware="DE",Florida="FL",Georgia="GA",Hawaii="HI",Idaho="ID",Illinois="IL",Indiana="IN",Iowa="IA",Kansas="KS",Kentucky="KY",Louisiana="LA",Maine="ME",Maryland="MD",Massachusetts="MA",Michigan="MI",Minnesota="MN",Mississippi="MS",Missouri="MO",Montana="MT",Nebraska="NE",Nevada="NV",**{"New Hampshire":"NH","New Jersey":"NJ","New Mexico":"NM","New York":"NY","North Carolina":"NC","North Dakota":"ND","Rhode Island":"RI","South Carolina":"SC","South Dakota":"SD","West Virginia":"WV","Puerto Rico":"PR","District of Columbia":"DC"},Ohio="OH",Oklahoma="OK",Oregon="OR",Pennsylvania="PA",Tennessee="TN",Texas="TX",Utah="UT",Vermont="VT",Virginia="VA",Washington="WA",Wisconsin="WI",Wyoming="WY")
states = []
for r in csv.DictReader(open(f'{R}/costco_state_revenue_estimate.csv')):
    states.append({"name": r["state"], "abbr": abbr[r["state"]], "warehouses": int(r["warehouses_costco_com_2026-10-26"]),
                   "value": int(r["est_FY2026_revenue_usd_millions"]) * 1e6, "anchored": r["state"] == "California"})

V = lambda m: m * 1e6
tl = lambda d, e, w="", s=(), verify=False: {"date": d, "text": e, "where": w, "src": list(s), **({"verify": True} if verify else {})}

data = {
 "type": "company", "slug": "costco", "live": True,
 "name": "Costco", "ticker_symbol": "COST", "legal_name": "Costco Wholesale Corporation",
 "title": "How Costco makes money, live: revenue, profit and where it goes",
 "description": "Costco's $303.2B year as a live clock: where the money comes from, where it goes, per employee, by country and state, and the decisions behind it. From the FY2026 10-K.",
 "tagline": "A warehouse club that earns about half its operating profit from membership fees.",
 "card_stat": {"label": "Revenue per second", "value": "$9,639", "note": "FY2026 10-K average"},
 "as_of": "Fiscal year ended Aug 30, 2026 (10-K filed Oct 7, 2026)",
 "sources": src,
 "sections": [
  {"id": "ticker", "title": "Costco, live", "blocks": [
    {"type": "ticker", "period_seconds": 31449600, "period_label": "FY2026 (364 days)",
     "label": "projected from annual 10-K averages",
     "counters": [
       {"id": "rev", "label": "Revenue", "annual": V(303154), "unit": "usd", "hero": True},
       {"id": "ni", "label": "Net income (profit)", "annual": V(9226), "unit": "usd"},
       {"id": "mem", "label": "Membership fees", "annual": V(5907), "unit": "usd"},
       {"id": "div", "label": "Dividends paid", "annual": V(2458), "unit": "usd"}],
     "note": "Each counter = FY2026 total from the 10-K ÷ 31,449,600 seconds (364 days). These are averages, not real-time sales. [[10k]]",
     "facts": [["Warehouses", "939"], ["Paid members", "84.1M"], ["Employees", "355,000"], ["Countries", "14"]]}
  ]},
  {"id": "flow", "title": "Money in, money out", "lede": "Every dollar of FY2026 revenue, from where it came to where it went. Values in US$ billions.", "blocks": [
    {"type": "sankey", "title": "Income statement, FY2026", "unit": "B", "scale": 1e-3,
     "nodes": [
       {"id": "fs", "label": "Foods & Sundries", "col": 0, "kind": "in"},
       {"id": "nf", "label": "Non-Foods", "col": 0, "kind": "in"},
       {"id": "ff", "label": "Fresh Foods", "col": 0, "kind": "in"},
       {"id": "an", "label": "Gas, pharmacy, optical, travel & other", "col": 0, "kind": "in"},
       {"id": "mf", "label": "Membership fees", "col": 0, "kind": "key"},
       {"id": "rev", "label": "Total revenue", "col": 1, "kind": "mid"},
       {"id": "mc", "label": "Merchandise costs", "col": 2, "kind": "cost"},
       {"id": "sga", "label": "Wages, benefits & other SG&A", "col": 2, "kind": "cost"},
       {"id": "oi", "label": "Operating income", "col": 2, "kind": "profit"},
       {"id": "int", "label": "Interest & other, net", "col": 2, "kind": "in"},
       {"id": "pt", "label": "Pre-tax income", "col": 3, "kind": "profit"},
       {"id": "tax", "label": "Income tax", "col": 4, "kind": "cost"},
       {"id": "ni", "label": "Net income", "col": 4, "kind": "profit"}],
     "links": [["fs","rev",116788],["nf","rev",77375],["ff","rev",41715],["an","rev",61369],["mf","rev",5907],
               ["rev","mc",264279],["rev","sga",27190],["rev","oi",11685],
               ["oi","pt",11685],["int","pt",566],["pt","tax",3025],["pt","ni",9226]],
     "note": "Net sales by category and all lines in US$ millions from the 10-K: 116,788 + 77,375 + 41,715 + 61,369 = 297,247 net sales; + 5,907 membership = 303,154. Interest & other, net = 711 interest income & other − 145 interest expense = 566 (derived). [[10k]]"},
    {"type": "sankey", "title": "Where the cash went, FY2026", "unit": "B", "scale": 1e-3,
     "nodes": [
       {"id": "ocf", "label": "Operating cash flow", "col": 0, "kind": "mid"},
       {"id": "capex", "label": "New warehouses & equipment (capex)", "col": 1, "kind": "cost"},
       {"id": "div", "label": "Dividends", "col": 1, "kind": "key"},
       {"id": "bb", "label": "Buybacks", "col": 1, "kind": "key"},
       {"id": "rest", "label": "Left over (mostly kept as cash)", "col": 1, "kind": "profit"}],
     "links": [["ocf","capex",6435],["ocf","div",2458],["ocf","bb",848],["ocf","rest",6076]],
     "note": "Capex 6,435 (US 5,122 · Canada 673 · Other International 640); dividends 2,458 ($5.54/share); buybacks 848. \"Left over\" = 15,817 − 6,435 − 2,458 − 848 = 6,076 (derived). Cash and short-term investments rose from 15,284 to 21,301. No special dividend in FY2026; the last was $15/share (~$6.7B) in FY2024. [[10k]]"},
    {"type": "stats", "items": [
       ["Gross margin on net sales", "11.09%", "[[10k]]"],
       ["Operating margin", "3.85%", "[[10k]]"],
       ["Effective tax rate", "24.7%", "Cash taxes paid: $2.84B [[10k]]"],
       ["Free cash flow", "$9.4B", "15,817 − 6,435 (derived) [[10k]]"]]}
  ]},
  {"id": "employees", "title": "Per employee", "lede": "355,000 employees at fiscal year-end; 95% work in warehouses and distribution. [[10k]]", "blocks": [
    {"type": "stats", "items": [
       ["Revenue per employee", "$853,955", "303,154M ÷ 355,000 [[10k]]"],
       ["Profit per employee", "$25,989", "Net income ÷ employees [[10k]]"],
       ["Operating income per employee", "$32,915", "[[10k]]"],
       ["Average hourly wage, US/Canada", "~$31", "\"a little more than $31\" incl. bonuses; top of scale $31.90 [[cfodive]]"],
       ["Retention, 1+ year employees", "~94%", "US and Canada [[10k]]"],
       ["Full-time share", "Not disclosed", "The 10-K only states a target of at least 50% full-time [[10k]]"]]}
  ]},
  {"id": "geography", "title": "Where the money comes from", "lede": "Costco reports three segments. Revenue inside \"Other International\" and by US state is not disclosed.", "blocks": [
    {"type": "bars", "title": "Total revenue by segment, FY2026", "unit": "usd", "items": [
       ["United States (incl. Puerto Rico)", V(219823)], ["Canada", V(40561)], ["Other International", V(42770)]], "src": ["10k"]},
    {"type": "table", "title": "Segments", "cols": ["Segment", "Revenue", "Op. income", "Warehouses", "Employees", "Floor space"],
     "align": "lrrrrr",
     "rows": [["United States", "$219.8B", "$7.65B", "647", "232,000", "96.6M sq ft"],
              ["Canada", "$40.6B", "$2.11B", "115", "58,000", "16.6M sq ft"],
              ["Other International", "$42.8B", "$1.93B", "177", "65,000", "25.5M sq ft"],
              ["Total", "$303.2B", "$11.69B", "939", "355,000", "138.7M sq ft"]], "src": ["10k"]},
    {"type": "table", "title": "Other International warehouses by country", "cols": ["Country", "Warehouses"], "align": "lr", "compact": True,
     "rows": [["Mexico","43"],["Japan","37"],["United Kingdom","29"],["South Korea","20"],["Australia","15"],["Taiwan","14"],["China","7"],["Spain","5"],["France","3"],["Sweden","2"],["Iceland","1"],["New Zealand","1"]],
     "note": "Revenue per country is not disclosed, so none is shown. [[10k]]"},
    {"type": "statemap", "title": "US revenue by state, FY2026", "estimate": True, "items": states,
     "banner": "ESTIMATE, not reported by Costco. Only California's share is disclosed.",
     "method": ["California = 26% of US segment revenue ($219.8B) = $57.2B. The 10-K says California was 26% of US net sales. [[10k]]",
                "Every other state = (US revenue − California) × its share of the 499 non-California warehouses ≈ $326M per warehouse. [[wh]]",
                "Ignores e-commerce, mid-year openings and differences in gas and business-center sales. Warehouse counts are from costco.com (636 listed vs 647 in the 10-K; DC not listed)."],
     "note": "California's implied ~$417M per warehouse vs ~$326M elsewhere matches the 10-K's note that California has more high-volume warehouses. California was also 39% of Costco's US state/local cash income tax ($209M of $531M). [[10k]]"}
  ]},
  {"id": "decisions", "title": "The decisions behind the numbers", "blocks": [
    {"type": "cards", "items": [
      {"kicker": "Membership model", "big": "~51%", "title": "of operating income from 1.9% of revenue",
       "text": "Membership fees were $5.9B, under 2% of revenue but about half of operating income (5,907 ÷ 11,685, derived). 84.1M paid members renew at 92.3% in the US and Canada and 89.8% worldwide. Executive members drove ~75.2% of net sales.", "src": ["10k"]},
      {"kicker": "Markup cap", "big": "14% / 15%", "title": "max markup on branded / Kirkland items",
       "text": "\"No branded product is marked up by more than 14% and no Kirkland Signature product by more than 15%.\" The result: an 11.09% gross margin on net sales in FY2026.", "src": ["markup", "10k"]},
      {"kicker": "Kirkland Signature", "big": "~$86B", "title": "in 2024 sales",
       "text": "Launched in October 1995 with about two dozen items. The 10-K gives no dollar figure; the ~$86B estimate is from The Wall Street Journal.", "src": ["sn", "wsj_kirkland"]},
      {"kicker": "The $1.50 hot dog", "big": "$1.50", "title": "hot dog + soda since 1985",
       "text": "The combo price hasn't changed since 1985. To hold it, Costco brought hot dog production in-house.", "src": ["fortune", "wsj_hotdog"]},
      {"kicker": "Wages and retention", "big": "~94%", "title": "retention after the first year",
       "text": "Average hourly pay in the US and Canada is a little over $31 including bonuses. Retention is about 94% for employees with a year or more. All overhead (SG&A, mostly wages and benefits) was 8.97% of revenue (27,190 ÷ 303,154, derived).", "src": ["cfodive", "10k"]}
    ]}
  ]},
  {"id": "timeline", "title": "Timeline", "lede": "Big events, breakthroughs, people and places.", "blocks": [
    {"type": "timeline", "items": [
      tl("1954", "Sol Price founds FedMart, a membership discount store. Jim Sinegal starts there as a bagger.", "San Diego, CA", ["wiki"], True),
      tl("Jul 12, 1976", "Price Club opens: the first membership warehouse club, in a converted Howard Hughes aircraft hangar. It still operates as Costco #401.", "Sol & Robert Price · San Diego, CA", ["about", "wiki"]),
      tl("Sep 15, 1983", "The first Costco warehouse opens.", "Jim Sinegal & Jeff Brotman · Seattle, WA", ["about", "10k"]),
      tl("1985", "The $1.50 hot dog and soda combo starts. The price hasn't changed since.", "", ["fortune"]),
      tl("1985", "Costco enters Canada.", "Burnaby, BC", ["wiki"], True),
      tl("Dec 5, 1985", "IPO on NASDAQ at $10 a share (about $1.67 split-adjusted).", "", ["irfaq"]),
      tl("1987", "Headquarters moves to Kirkland, WA, later the source of the Kirkland Signature name.", "Kirkland, WA", ["wiki"]),
      tl("1992", "Price Club enters Mexico in a joint venture with Comercial Mexicana.", "Mexico City", ["wiki"]),
      tl("Oct 21, 1993", "Merges with Price Club to form PriceCostco: 206 locations, $16B in sales.", "", ["irfaq", "about"]),
      tl("1993", "Enters the UK.", "Thurrock", [], True),
      tl("1994", "The Price family leaves to form PriceSmart. Rotisserie chicken starts.", "", ["wiki"]),
      tl("1994", "Enters South Korea.", "Seoul", ["wiki"], True),
      tl("Oct 1995", "Kirkland Signature launches with about two dozen items.", "", ["sn"]),
      tl("1996", "Headquarters moves to Issaquah, WA.", "Issaquah, WA", ["wiki"]),
      tl("Feb 1997", "Renamed Costco Companies; ticker COST.", "", ["irfaq"]),
      tl("1997", "Enters Taiwan.", "", [], True),
      tl("1998", "Costco.com launches.", "", ["wiki"]),
      tl("1999", "Enters Japan.", "", [], True),
      tl("Aug 30, 1999", "Renamed Costco Wholesale Corp. and reincorporated in Washington.", "", ["irfaq"]),
      tl("May 2006", "Gold Star membership fee rises from $45 to $50.", "", ["pr"], True),
      tl("2009", "Enters Australia.", "Melbourne Docklands", ["wiki"]),
      tl("Nov 2011", "Membership fee rises from $50 to $55.", "", [], True),
      tl("Jan 1, 2012", "Sinegal retires; Craig Jelinek becomes CEO.", "", ["wiki"]),
      tl("Dec 2012", "Special dividend of $7 a share.", "", ["pr"], True),
      tl("2014", "Enters Spain; opens an online store in China on Alibaba's Tmall.", "", ["wiki"]),
      tl("Jan 30, 2015", "Special dividend of $5 a share.", "", ["pr"]),
      tl("2016", "US co-branded credit card moves from American Express to Citi/Visa.", "", ["wiki"]),
      tl("Apr 25, 2017", "Special dividend of $7 a share.", "", ["pr"]),
      tl("Jun 2017", "Membership fee rises from $55 to $60 (Executive $110 → $120).", "", ["wiki"]),
      tl("Aug 1, 2017", "Co-founder Jeff Brotman dies; Hamilton James later becomes chairman.", "", ["wiki"]),
      tl("2017", "Enters France and Iceland.", "", [], True),
      tl("Aug 27, 2019", "First mainland China warehouse opens.", "Shanghai", ["wiki"]),
      tl("Dec 2020", "Special dividend of $10 a share.", "", ["pr"], True),
      tl("Sep 2022", "Enters New Zealand.", "West Auckland", ["wiki"]),
      tl("Oct 2023", "Starts selling 1-oz gold bars.", "", ["wiki"]),
      tl("Jan 1, 2024", "Ron Vachris becomes CEO, only the third. He started in 1982 as a Price Club forklift driver.", "", ["wiki"]),
      tl("Jan 2024", "Special dividend of $15 a share, about $6.7B.", "", ["10k"]),
      tl("Sep 1, 2024", "Membership fee rises from $60 to $65 (Executive $120 → $130).", "", ["wiki"]),
      tl("2024", "Enters Sweden.", "Stockholm", [], True),
      tl("FY2026", "939 warehouses in 14 countries, $303.2B revenue, 355,000 employees, 84.1M paid members.", "", ["10k"]),
    ], "note": "Several entries currently rest on Wikipedia; they should be checked against Costco's own filings and releases before launch."}
  ]},
 ]
}
json.dump(data, open(f'{HERE}/data/costco.json', 'w'), indent=1, ensure_ascii=False)
print('wrote data/costco.json', len(states), 'states')
