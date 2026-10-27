"""Regenerate data/apple.json, data/amazon.json, data/amex.json.
Every figure is copied from the company's latest 10-K (SEC EDGAR) or the SEC XBRL companyfacts API
(https://data.sec.gov/api/xbrl/companyfacts/), in US$ millions. Derived values are computed here and labelled "derived".
Re-run:  python3 tools/seed_companies.py && python3 build.py"""
import json, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = lambda m: m * 1e6
def B(m, d=1): return f"${m/1000:,.{d}f}B"
def K(m, n): return f"${m*1e6/n/1e3:,.0f}K"          # m in $M, n employees in units
def P(a, b, d=1): return f"{a/b*100:.{d}f}%"
tl = lambda d, e, s=(): {"date": d, "text": e, "where": "", "src": list(s)}
def write(slug, data):
    json.dump(data, open(f'{HERE}/data/{slug}.json', 'w'), indent=1, ensure_ascii=False)
    print('wrote', slug)
def per_sec(m, secs): return f"${m*1e6/secs:,.0f}"

# =============================================================== APPLE
A = dict(rev=416161, prod=307003, serv=109158, iphone=209586, mac=33708, ipad=28023, wear=35686,
         cogs=220960, cogs_p=194116, cogs_s=26844, gm=195201, gm_p=112887, gm_s=82314, rd=34550, sga=27601, oi=133050, oth=-321, pt=132729,
         tax=20719, ni=112010, ocf=111482, capex=12715, div=15421, bb=90711, emp=166000)
assert A['iphone']+A['mac']+A['ipad']+A['wear']+A['serv']==A['rev']
assert A['cogs']+A['rd']+A['sga']+A['oi']==A['rev'] and A['oi']+A['oth']==A['pt'] and A['pt']-A['tax']==A['ni']
short = A['capex']+A['div']+A['bb']-A['ocf']           # 7,365 covered from cash, securities and debt
APS = 31449600
apple_src = {
 "10k": ["Apple Inc., Form 10-K for the fiscal year ended Sep 27, 2025 (filed Oct 31, 2025)", "https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm"],
 "facts": ["SEC EDGAR XBRL companyfacts, Apple Inc. (CIK 0000320193): annual revenue and net income from each year's 10-K", "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json"],
 "filings": ["SEC EDGAR: Apple Inc. filings", "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193&type=10-K"],
}
apple = {
 "type": "company", "slug": "apple", "order": 10, "live": True, "name": "Apple", "ticker_symbol": "AAPL", "legal_name": "Apple Inc.",
 "title": "How Apple makes money, live: revenue, profit and where it goes",
 "description": f"Apple's {B(A['rev'])} year as a live clock: iPhone, Mac, iPad and Services revenue, where the money goes, buybacks and dividends, per employee and by region. From the FY2025 10-K.",
 "tagline": f"The iPhone is half of sales, but Services is {P(A['serv'],A['rev'],0)} of revenue and {P(A['gm_s'],A['gm'],0)} of gross profit.",
 "card_stat": {"label": "Revenue per second", "value": per_sec(A['rev'], APS), "note": "FY2025 10-K average"},
 "as_of": "Fiscal year ended Sep 27, 2025 (10-K filed Oct 31, 2025)",
 "sources": apple_src,
 "sections": [
  {"id": "ticker", "title": "Apple, live", "blocks": [
    {"type": "ticker", "period_seconds": APS, "period_label": "FY2025 (364 days)", "label": "projected from annual 10-K averages",
     "counters": [
       {"id": "rev", "label": "Revenue", "annual": V(A['rev']), "unit": "usd", "hero": True},
       {"id": "ni", "label": "Net income (profit)", "annual": V(A['ni']), "unit": "usd"},
       {"id": "bb", "label": "Share buybacks", "annual": V(A['bb']), "unit": "usd"},
       {"id": "div", "label": "Dividends paid", "annual": V(A['div']), "unit": "usd"}],
     "note": f"Each counter = FY2025 total from the 10-K ÷ {APS:,} seconds (364 days, the 52-week fiscal year). These are averages, not real-time sales. Buybacks and dividends are the cash paid in the cash flow statement. [[10k]]",
     "facts": [["Employees", "~166,000"], ["Quarterly dividend", "$0.26"], ["Cash & securities", "$132.4B"], ["Diluted EPS", "$7.46"]]}
  ]},
  {"id": "flow", "title": "Money in, money out", "lede": "Every dollar of FY2025 revenue, from where it came to where it went. Values in US$ billions.", "blocks": [
    {"type": "sankey", "title": "Income statement, FY2025", "unit": "B", "scale": 1e-3,
     "nodes": [
       {"id": "ip", "label": "iPhone", "col": 0, "kind": "in"}, {"id": "mac", "label": "Mac", "col": 0, "kind": "in"},
       {"id": "ipad", "label": "iPad", "col": 0, "kind": "in"}, {"id": "wh", "label": "Wearables, Home & Accessories", "col": 0, "kind": "in"},
       {"id": "sv", "label": "Services", "col": 0, "kind": "key"},
       {"id": "rev", "label": "Total revenue", "col": 1, "kind": "mid"},
       {"id": "cs", "label": "Cost of sales", "col": 2, "kind": "cost"}, {"id": "rd", "label": "Research & development", "col": 2, "kind": "cost"},
       {"id": "sga", "label": "Selling, general & admin", "col": 2, "kind": "cost"}, {"id": "oi", "label": "Operating income", "col": 2, "kind": "profit"},
       {"id": "pt", "label": "Pre-tax income", "col": 3, "kind": "profit"}, {"id": "oth", "label": "Other expense, net", "col": 3, "kind": "cost"},
       {"id": "tax", "label": "Income tax", "col": 4, "kind": "cost"}, {"id": "ni", "label": "Net income", "col": 4, "kind": "profit"}],
     "links": [["ip","rev",A['iphone']],["mac","rev",A['mac']],["ipad","rev",A['ipad']],["wh","rev",A['wear']],["sv","rev",A['serv']],
               ["rev","cs",A['cogs']],["rev","rd",A['rd']],["rev","sga",A['sga']],["rev","oi",A['oi']],
               ["oi","pt",A['pt']],["oi","oth",-A['oth']],["pt","tax",A['tax']],["pt","ni",A['ni']]],
     "note": f"US$ millions from the 10-K: 209,586 + 33,708 + 28,023 + 35,686 + 109,158 = 416,161 net sales. Cost of sales 220,960 (products 194,116, services 26,844). Operating income 133,050 less other expense, net 321 = pre-tax 132,729 (derived); tax 20,719; net income 112,010. [[10k]]"},
    {"type": "sankey", "title": "Where the cash went, FY2025", "unit": "B", "scale": 1e-3,
     "nodes": [
       {"id": "ocf", "label": "Operating cash flow", "col": 0, "kind": "mid"},
       {"id": "gap", "label": "Drawn from cash, securities & debt", "col": 0, "kind": "in"},
       {"id": "capex", "label": "Capex (property, plant & equipment)", "col": 1, "kind": "cost"},
       {"id": "div", "label": "Dividends", "col": 1, "kind": "key"}, {"id": "bb", "label": "Buybacks", "col": 1, "kind": "key"}],
     "links": [["ocf","capex",A['capex']],["ocf","div",A['div']],["ocf","bb",A['ocf']-A['capex']-A['div']],["gap","bb",short]],
     "note": f"Operating cash flow 111,482; capex 12,715; dividends and dividend equivalents 15,421; common stock repurchased 90,711 (cash basis; the 10-K MD&A says $89.3B of shares repurchased, 402 million shares). Apple paid out {short:,} more than it generated: 12,715 + 15,421 + 90,711 − 111,482 = {short:,} (derived), funded from cash, marketable securities and net debt activity. [[10k]]"},
    {"type": "stats", "items": [
       ["Gross margin", P(A['gm'],A['rev']), "195,201 ÷ 416,161 [[10k]]"],
       ["Operating margin", P(A['oi'],A['rev']), "133,050 ÷ 416,161 (derived) [[10k]]"],
       ["Effective tax rate", "15.6%", "24.1% a year earlier, which included a State Aid charge [[10k]]"],
       ["Free cash flow", B(A['ocf']-A['capex']), "111,482 − 12,715 (derived) [[10k]]"]]}
  ]},
  {"id": "employees", "title": "Per employee", "lede": "About 166,000 full-time equivalent employees at fiscal year-end. [[10k]]", "blocks": [
    {"type": "stats", "items": [
       ["Revenue per employee", K(A['rev'],A['emp']).replace('K','K'), "416,161M ÷ 166,000 [[10k]]"],
       ["Profit per employee", K(A['ni'],A['emp']), "Net income ÷ employees [[10k]]"],
       ["Operating income per employee", K(A['oi'],A['emp']), "[[10k]]"],
       ["R&D per employee", K(A['rd'],A['emp']), "34,550M ÷ 166,000 [[10k]]"],
       ["Avg. hourly wage", "Not disclosed", "The 10-K gives headcount only, no pay data [[10k]]"]]}
  ]},
  {"id": "geography", "title": "Where the money comes from", "lede": "Apple reports five geographic segments, and sales by product category. It does not disclose revenue by US state.", "blocks": [
    {"type": "bars", "title": "Net sales by product category, FY2025", "unit": "usd", "items": [
       ["iPhone", V(A['iphone'])], ["Services", V(A['serv'])], ["Wearables, Home & Accessories", V(A['wear'])], ["Mac", V(A['mac'])], ["iPad", V(A['ipad'])]], "src": ["10k"]},
    {"type": "bars", "title": "Net sales by region, FY2025", "unit": "usd", "items": [
       ["Americas", V(178353)], ["Europe (incl. India, Middle East, Africa)", V(111032)], ["Greater China", V(64377)], ["Rest of Asia Pacific", V(33696)], ["Japan", V(28703)]], "src": ["10k"]},
    {"type": "table", "title": "Segments, FY2025", "cols": ["Segment", "Net sales", "Operating income", "Margin"], "align": "lrrr",
     "rows": [["Americas", "$178.4B", "$72.5B", P(72480,178353)], ["Europe", "$111.0B", "$47.7B", P(47739,111032)], ["Greater China", "$64.4B", "$26.9B", P(26917,64377)],
              ["Japan", "$28.7B", "$14.0B", P(13955,28703)], ["Rest of Asia Pacific", "$33.7B", "$14.6B", P(14586,33696)]],
     "src": ["10k"], "note": "Segment operating income excludes R&D ($34.6B) and general & administrative ($8.1B), which are held at corporate. Margins are derived. [[10k]]"},
    {"type": "table", "title": "By country", "cols": ["", "Net sales", "Share", "Long-lived assets"], "align": "lrrr", "compact": True,
     "rows": [["United States", "$151.8B", P(151790,A['rev']), "$40.3B"], ["China (incl. Hong Kong, Taiwan)", "$64.4B", P(64377,A['rev']), "$3.6B"], ["Other countries", "$200.0B", P(199994,A['rev']), "$5.9B"]],
     "src": ["10k"], "note": "Only the US and China are 10% or more of sales, so only they are broken out. Share is derived. [[10k]]"}
  ]},
  {"id": "decisions", "title": "The decisions behind the numbers", "blocks": [
    {"type": "cards", "items": [
      {"kicker": "Services", "big": P(A['gm_s'],A['gm'],0), "title": f"of gross profit from {P(A['serv'],A['rev'],0)} of revenue",
       "text": f"Services sales were $109.2B (up 14%) with a 75.4% gross margin, against 36.8% for products. That is $82.3B of the $195.2B total gross margin (derived). The 10-K credits advertising, the App Store and cloud services for the growth.", "src": ["10k"]},
      {"kicker": "Buybacks", "big": "$89.3B", "title": "of stock repurchased in FY2025",
       "text": "402 million shares retired. In May 2025 Apple announced a new $100B program and raised the quarterly dividend from $0.25 to $0.26. Cash returned (buybacks 90.7B + dividends 15.4B) was 95% of net income (derived).", "src": ["10k"]},
      {"kicker": "Greater China", "big": "−4%", "title": "sales fell to $64.4B",
       "text": "Greater China net sales were $72.6B in FY2023, $67.0B in FY2024 and $64.4B in FY2025, now 15% of the total (derived). The 10-K attributes the FY2025 drop mainly to lower iPhone sales.", "src": ["10k"]},
      {"kicker": "Research and development", "big": P(A['rd'],A['rev']), "title": "of revenue goes to R&D",
       "text": "R&D was $34.6B, up 10%, and R&D plus SG&A ($62.2B) was 14.9% of revenue (derived). Cost of sales alone took 53%.", "src": ["10k"]},
      {"kicker": "Taxes", "big": "15.6%", "title": "effective tax rate, versus 24.1% a year earlier",
       "text": "FY2024's rate included the State Aid Decision charge. The 10-K says the provision fell $10.7B year over year on that item. Cash taxes paid were $43.4B in FY2025.", "src": ["10k"]}
    ]}
  ]},
  {"id": "timeline", "title": "Five years of results", "lede": "Revenue and net income by fiscal year, from the 10-Ks.", "blocks": [
    {"type": "timeline", "items": [
      tl("FY2021", "Revenue $365.8B, net income $94.7B.", ["facts"]), tl("FY2022", "Revenue $394.3B, net income $99.8B. Buybacks $89.4B, dividends $14.8B.", ["facts"]),
      tl("FY2023", "Revenue $383.3B (down 3%), net income $97.0B. Buybacks $77.6B.", ["10k", "facts"]), tl("FY2024", "Revenue $391.0B, net income $93.7B after the State Aid charge. Buybacks $94.9B.", ["10k"]),
      tl("FY2025", "Revenue $416.2B (up 6%), net income $112.0B, a five-year high. Buybacks $90.7B, dividends $15.4B.", ["10k"])]}
  ]},
 ]}
write('apple', apple)

# =============================================================== AMAZON
Z = dict(online=269287, phys=22561, tp=172162, ads=68635, subs=49619, aws=128725, other=5935, rev=716924,
         cos=356414, ful=109074, tech=108521, sm=47129, ga=11172, oox=4639, oi=79975, nonop=17336, pt=97311, tax=19087, eq=554, ni=77670,
         ocf=139514, capex=131819, proceeds=3499, emp=1576000)
assert sum(Z[k] for k in ('online','phys','tp','ads','subs','aws','other'))==Z['rev']
assert Z['cos']+Z['ful']+Z['tech']+Z['sm']+Z['ga']+Z['oox']+Z['oi']==Z['rev']
assert Z['oi']+Z['nonop']==Z['pt'] and Z['pt']-Z['tax']-Z['eq']==Z['ni']
ZS = 31536000
fcf = Z['ocf']-(Z['capex']-Z['proceeds']); assert fcf==11194
amazon_src = {
 "10k": ["Amazon.com, Inc., Form 10-K for the year ended Dec 31, 2025 (filed Feb 6, 2026)", "https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm"],
 "facts": ["SEC EDGAR XBRL companyfacts, Amazon.com, Inc. (CIK 0001018724): annual figures from each year's 10-K", "https://data.sec.gov/api/xbrl/companyfacts/CIK0001018724.json"],
}
amazon = {
 "type": "company", "slug": "amazon", "order": 20, "live": True, "name": "Amazon", "ticker_symbol": "AMZN", "legal_name": "Amazon.com, Inc.",
 "title": "How Amazon makes money, live: revenue, AWS, ads and where it goes",
 "description": f"Amazon's {B(Z['rev'])} year as a live clock: online stores, third-party sellers, ads, Prime and AWS, where the money goes, capex, and per employee. From the FY2025 10-K.",
 "tagline": f"AWS is {P(Z['aws'],Z['rev'],0)} of sales but {P(45606,Z['oi'],0)} of operating income. Capex hit $131.8B.",
 "card_stat": {"label": "Revenue per second", "value": per_sec(Z['rev'], ZS), "note": "FY2025 10-K average"},
 "as_of": "Year ended Dec 31, 2025 (10-K filed Feb 6, 2026)",
 "sources": amazon_src,
 "sections": [
  {"id": "ticker", "title": "Amazon, live", "blocks": [
    {"type": "ticker", "period_seconds": ZS, "period_label": "2025 (365 days)", "label": "projected from annual 10-K averages",
     "counters": [
       {"id": "rev", "label": "Revenue", "annual": V(Z['rev']), "unit": "usd", "hero": True},
       {"id": "ni", "label": "Net income (profit)", "annual": V(Z['ni']), "unit": "usd"},
       {"id": "aws", "label": "AWS revenue", "annual": V(Z['aws']), "unit": "usd"},
       {"id": "capex", "label": "Capital spending", "annual": V(Z['capex']), "unit": "usd"}],
     "note": f"Each counter = 2025 total from the 10-K ÷ {ZS:,} seconds. These are averages, not real-time sales. Capital spending = purchases of property and equipment in the cash flow statement ($131.8B, before $3.5B of proceeds and incentives). [[10k]]",
     "facts": [["Employees", "~1,576,000"], ["Dividends paid", "None"], ["Buybacks 2023–2025", "None"], ["Cash & securities", "$123.0B"]]}
  ]},
  {"id": "flow", "title": "Money in, money out", "lede": "Every dollar of 2025 revenue, from where it came to where it went. Values in US$ billions.", "blocks": [
    {"type": "sankey", "title": "Income statement, 2025", "unit": "B", "scale": 1e-3,
     "nodes": [
       {"id": "on", "label": "Online stores", "col": 0, "kind": "in"}, {"id": "ph", "label": "Physical stores", "col": 0, "kind": "in"},
       {"id": "tp", "label": "Third-party seller services", "col": 0, "kind": "in"}, {"id": "ad", "label": "Advertising", "col": 0, "kind": "key"},
       {"id": "sb", "label": "Subscriptions (Prime etc.)", "col": 0, "kind": "in"}, {"id": "aws", "label": "AWS", "col": 0, "kind": "key"}, {"id": "ot", "label": "Other", "col": 0, "kind": "in"},
       {"id": "rev", "label": "Total revenue", "col": 1, "kind": "mid"},
       {"id": "cos", "label": "Cost of sales", "col": 2, "kind": "cost"}, {"id": "ful", "label": "Fulfillment", "col": 2, "kind": "cost"},
       {"id": "tech", "label": "Technology & infrastructure", "col": 2, "kind": "cost"}, {"id": "sm", "label": "Sales & marketing", "col": 2, "kind": "cost"},
       {"id": "ga", "label": "G&A and other operating", "col": 2, "kind": "cost"}, {"id": "oi", "label": "Operating income", "col": 2, "kind": "profit"},
       {"id": "no", "label": "Interest & other income, net", "col": 2, "kind": "in"},
       {"id": "pt", "label": "Pre-tax income", "col": 3, "kind": "profit"},
       {"id": "tax", "label": "Income tax & equity-method", "col": 4, "kind": "cost"}, {"id": "ni", "label": "Net income", "col": 4, "kind": "profit"}],
     "links": [["on","rev",Z['online']],["ph","rev",Z['phys']],["tp","rev",Z['tp']],["ad","rev",Z['ads']],["sb","rev",Z['subs']],["aws","rev",Z['aws']],["ot","rev",Z['other']],
               ["rev","cos",Z['cos']],["rev","ful",Z['ful']],["rev","tech",Z['tech']],["rev","sm",Z['sm']],["rev","ga",Z['ga']+Z['oox']],["rev","oi",Z['oi']],
               ["oi","pt",Z['oi']],["no","pt",Z['nonop']],["pt","tax",Z['tax']+Z['eq']],["pt","ni",Z['ni']]],
     "note": f"US$ millions from the 10-K: 269,287 + 22,561 + 172,162 + 68,635 + 49,619 + 128,725 + 5,935 = 716,924 net sales. \"G&A and other\" = G&A 11,172 + other operating expense 4,639 (includes a $2.5B FTC settlement charge). Non-operating income, net of 17,336 = interest income 4,381 − interest expense 2,274 + other income 15,229, which the 10-K attributes mainly to equity-investment valuation adjustments, not cash from selling goods. \"Income tax & equity-method\" = 19,087 + 554. [[10k]]"},
    {"type": "sankey", "title": "Where the cash went, 2025", "unit": "B", "scale": 1e-3,
     "nodes": [
       {"id": "ocf", "label": "Operating cash flow", "col": 0, "kind": "mid"},
       {"id": "capex", "label": "Capex, net of sale proceeds & incentives", "col": 1, "kind": "cost"},
       {"id": "fcf", "label": "Free cash flow (what was left)", "col": 1, "kind": "profit"}],
     "links": [["ocf","capex",Z['capex']-Z['proceeds']],["ocf","fcf",fcf]],
     "note": "Operating cash flow 139,514 − purchases of property and equipment 131,819 + proceeds from sales and incentives 3,499 = free cash flow 11,194, as the 10-K defines it (it was 38,219 in 2024). Amazon paid no dividends (none in the cash flow statement) and made no buybacks in 2023, 2024 or 2025; $6.1B remains on the 2022 authorization. [[10k]]"},
    {"type": "stats", "items": [
       ["Operating margin", P(Z['oi'],Z['rev']), "79,975 ÷ 716,924 (derived) [[10k]]"],
       ["AWS operating margin", P(45606,Z['aws']), "45,606 ÷ 128,725 (derived) [[10k]]"],
       ["Effective tax rate", P(Z['tax'],Z['pt']), "19,087 ÷ 97,311 (derived); cash taxes paid $8.3B [[10k]]"],
       ["Free cash flow", B(fcf), "Down from $38.2B in 2024 [[10k]]"]]}
  ]},
  {"id": "employees", "title": "Per employee", "lede": "About 1,576,000 full-time and part-time employees at year-end, plus contractors and temporary staff that are not counted. [[10k]]", "blocks": [
    {"type": "stats", "items": [
       ["Revenue per employee", K(Z['rev'],Z['emp']), "716,924M ÷ 1,576,000 [[10k]]"],
       ["Profit per employee", K(Z['ni'],Z['emp']), "Net income ÷ employees; includes $15.2B of investment gains [[10k]]"],
       ["Operating income per employee", K(Z['oi'],Z['emp']), "[[10k]]"],
       ["Stock comp per employee", K(19467,Z['emp']), "$19.5B stock-based compensation ÷ employees (derived) [[10k]]"],
       ["Avg. hourly wage", "Not disclosed", "The 10-K gives headcount only, no pay data [[10k]]"]]}
  ]},
  {"id": "geography", "title": "Where the money comes from", "lede": "Amazon reports three segments, revenue by product and service group, and revenue by country. It does not disclose revenue by US state.", "blocks": [
    {"type": "bars", "title": "Net sales by group, 2025", "unit": "usd", "items": [
       ["Online stores", V(Z['online'])], ["Third-party seller services", V(Z['tp'])], ["AWS", V(Z['aws'])], ["Advertising services", V(Z['ads'])], ["Subscription services", V(Z['subs'])],
       ["Physical stores", V(Z['phys'])], ["Other", V(Z['other'])]], "src": ["10k"]},
    {"type": "bars", "title": "Net sales by country, 2025", "unit": "usd", "items": [
       ["United States", V(489657)], ["Germany", V(45900)], ["United Kingdom", V(43212)], ["Japan", V(30688)], ["Rest of world", V(107467)]], "src": ["10k"]},
    {"type": "table", "title": "Segments, 2025", "cols": ["Segment", "Net sales", "Operating income", "Margin"], "align": "lrrr",
     "rows": [["North America", "$426.3B", "$29.6B", P(29619,426305)], ["International", "$161.9B", "$4.8B", P(4750,161894)], ["AWS", "$128.7B", "$45.6B", P(45606,128725)], ["Total", "$716.9B", "$80.0B", P(79975,716924)]],
     "src": ["10k"], "note": "Margins are derived. AWS earns 57% of operating income (45,606 ÷ 79,975, derived). [[10k]]"}
  ]},
  {"id": "decisions", "title": "The decisions behind the numbers", "blocks": [
    {"type": "cards", "items": [
      {"kicker": "AWS", "big": P(45606,Z['oi'],0), "title": f"of operating income from {P(Z['aws'],Z['rev'],0)} of sales",
       "text": "AWS sales grew 20% to $128.7B at a 35.4% operating margin (derived). North America earned 7.0% and International 2.9%. Retail and AWS are different businesses in one filing.", "src": ["10k"]},
      {"kicker": "Capital spending", "big": "$131.8B", "title": "of capex, up from $83.0B",
       "text": "Purchases of property and equipment were $52.7B in 2023, $83.0B in 2024 and $131.8B in 2025. Of 2025's $142.4B total net additions, $96.5B went to AWS. Free cash flow fell from $38.2B to $11.2B.", "src": ["10k", "facts"]},
      {"kicker": "Advertising", "big": "$68.6B", "title": "of ad revenue, up 22%",
       "text": "Advertising sales grew from $46.9B in 2023 to $68.6B in 2025 (growth derived), now 9.6% of revenue (derived). The 10-K lists it as its own line.", "src": ["10k"]},
      {"kicker": "Third-party sellers", "big": "$172.2B", "title": "in seller services revenue",
       "text": "Commissions plus fulfillment and shipping fees on sellers' products were 24% of revenue (derived), second only to Amazon's own online stores ($269.3B, 38% of revenue, derived).", "src": ["10k"]},
      {"kicker": "One-time charges", "big": "$5.2B", "title": "of FTC settlement and severance in 2025",
       "text": "Operating income includes $2.5B for a settlement with the FTC and $2.7B of estimated severance costs, per the 10-K. Both are in the 2025 figures shown here.", "src": ["10k"]},
      {"kicker": "No payouts", "big": "$0", "title": "in buybacks 2023–2025, and no dividends",
       "text": "Amazon keeps its cash for investment. There were no repurchases in 2023, 2024 or 2025, and the cash flow statement has no dividend line.", "src": ["10k"]}
    ]}
  ]},
  {"id": "timeline", "title": "Five years of results", "lede": "Revenue, operating income and net income by year, from the 10-Ks.", "blocks": [
    {"type": "timeline", "items": [
      tl("2021", "Revenue $469.8B, operating income $24.9B, net income $33.4B. Capex $61.1B.", ["facts"]),
      tl("2022", "Revenue $514.0B, operating income $12.2B, a net loss of $2.7B, the only loss in the five years.", ["facts"]),
      tl("2023", "Revenue $574.8B, operating income $36.9B, net income $30.4B. Capex $52.7B.", ["10k"]),
      tl("2024", "Revenue $638.0B, operating income $68.6B, net income $59.2B. Capex $83.0B.", ["10k"]),
      tl("2025", "Revenue $716.9B (up 12%), operating income $80.0B, net income $77.7B. Capex $131.8B.", ["10k"])]}
  ]},
 ]}
write('amazon', amazon)

# =============================================================== AMERICAN EXPRESS
X = dict(disc=37401, fees=9993, svc=7471, ii=25598, ie=8234, nii=17364, rev=72229, prov=5256, rew=18409, bd=6457, cms=6057, mkt=6252, sal=9016, oth=6987, exp=53178,
         pt=13795, tax=2962, ni=10833, div=2271, bb=5311, emp=76800)
assert X['disc']+X['fees']+X['svc']+X['ii']-X['ie']==X['rev'] and X['rew']+X['bd']+X['cms']+X['mkt']+X['sal']+X['oth']==X['exp']
assert X['rev']-X['prov']-X['exp']==X['pt'] and X['pt']-X['tax']==X['ni']
gross = X['disc']+X['fees']+X['svc']+X['ii']
retained = X['ni']-X['div']-X['bb']
XS = 31536000
amex_src = {
 "10k": ["American Express Company, Form 10-K for the year ended Dec 31, 2025 (filed Feb 6, 2026)", "https://www.sec.gov/Archives/edgar/data/4962/000000496226000080/axp-20251231.htm"],
 "facts": ["SEC EDGAR XBRL companyfacts, American Express Co (CIK 0000004962): annual figures from each year's 10-K", "https://data.sec.gov/api/xbrl/companyfacts/CIK0000004962.json"],
}
amex = {
 "type": "company", "slug": "american-express", "order": 30, "live": True, "name": "American Express", "ticker_symbol": "AXP", "legal_name": "American Express Company",
 "title": "How American Express makes money, live: fees, interest and where it goes",
 "description": f"American Express's {B(X['rev'])} year as a live clock: merchant discount revenue, card fees and interest, rewards and credit costs, buybacks and dividends. From the FY2025 10-K.",
 "tagline": f"A card company that earns {P(X['disc'],X['rev'],0)} of its revenue from merchants, {P(X['fees'],X['rev'],0)} from card fees and {P(X['nii'],X['rev'],0)} from interest.",
 "card_stat": {"label": "Revenue per second", "value": per_sec(X['rev'], XS), "note": "FY2025 10-K average, net of interest expense"},
 "as_of": "Year ended Dec 31, 2025 (10-K filed Feb 6, 2026)",
 "sources": amex_src,
 "sections": [
  {"id": "ticker", "title": "American Express, live", "blocks": [
    {"type": "ticker", "period_seconds": XS, "period_label": "2025 (365 days)", "label": "projected from annual 10-K averages",
     "counters": [
       {"id": "rev", "label": "Revenue (net of interest expense)", "annual": V(X['rev']), "unit": "usd", "hero": True},
       {"id": "disc", "label": "Discount revenue (merchant fees)", "annual": V(X['disc']), "unit": "usd"},
       {"id": "fees", "label": "Net card fees", "annual": V(X['fees']), "unit": "usd"},
       {"id": "ni", "label": "Net income (profit)", "annual": V(X['ni']), "unit": "usd"}],
     "note": f"Each counter = 2025 total from the 10-K ÷ {XS:,} seconds. These are averages, not real-time. Revenue here is \"total revenues net of interest expense\", the 10-K's headline revenue line. [[10k]]",
     "facts": [["Spending on its cards", "$1.67T"], ["Cards in force", "86.6M"], ["Employees", "~76,800"], ["Dividends per share", "$3.28"]]}
  ]},
  {"id": "flow", "title": "Money in, money out", "lede": "A card company earns from merchants, cardholder fees and interest, and pays for funding, credit losses, rewards and marketing. Values in US$ billions.", "blocks": [
    {"type": "sankey", "title": "Income statement, 2025", "unit": "B", "scale": 1e-3,
     "nodes": [
       {"id": "disc", "label": "Discount revenue (merchant fees)", "col": 0, "kind": "key"}, {"id": "fees", "label": "Net card fees", "col": 0, "kind": "key"},
       {"id": "svc", "label": "Service fees & other revenue", "col": 0, "kind": "in"}, {"id": "ii", "label": "Interest income", "col": 0, "kind": "in"},
       {"id": "gross", "label": "Revenue before interest expense", "col": 1, "kind": "mid"},
       {"id": "ie", "label": "Interest expense", "col": 2, "kind": "cost"}, {"id": "net", "label": "Revenue net of interest expense", "col": 2, "kind": "mid"},
       {"id": "prov", "label": "Credit loss provisions", "col": 3, "kind": "cost"}, {"id": "rew", "label": "Card Member rewards", "col": 3, "kind": "cost"},
       {"id": "bd", "label": "Business development", "col": 3, "kind": "cost"}, {"id": "cms", "label": "Card Member services", "col": 3, "kind": "cost"},
       {"id": "mkt", "label": "Marketing", "col": 3, "kind": "cost"}, {"id": "sal", "label": "Salaries & benefits", "col": 3, "kind": "cost"},
       {"id": "oth", "label": "Other expenses", "col": 3, "kind": "cost"}, {"id": "pt", "label": "Pre-tax income", "col": 3, "kind": "profit"},
       {"id": "tax", "label": "Income tax", "col": 4, "kind": "cost"}, {"id": "ni", "label": "Net income", "col": 4, "kind": "profit"}],
     "links": [["disc","gross",X['disc']],["fees","gross",X['fees']],["svc","gross",X['svc']],["ii","gross",X['ii']],
               ["gross","ie",X['ie']],["gross","net",X['rev']],
               ["net","prov",X['prov']],["net","rew",X['rew']],["net","bd",X['bd']],["net","cms",X['cms']],["net","mkt",X['mkt']],["net","sal",X['sal']],["net","oth",X['oth']],["net","pt",X['pt']],
               ["pt","tax",X['tax']],["pt","ni",X['ni']]],
     "note": f"US$ millions from the 10-K: 37,401 + 9,993 + 7,471 + 25,598 = {gross:,} (derived) before interest expense of 8,234, leaving 72,229. Expenses: rewards 18,409 + business development 6,457 + Card Member services 6,057 + marketing 6,252 + salaries 9,016 + other 6,987 = 53,178. 72,229 − 5,256 provisions − 53,178 = 13,795 pre-tax. [[10k]]"},
    {"type": "sankey", "title": "Where the profit went, 2025", "unit": "B", "scale": 1e-3,
     "nodes": [
       {"id": "ni", "label": "Net income", "col": 0, "kind": "profit"},
       {"id": "bb", "label": "Share buybacks", "col": 1, "kind": "key"}, {"id": "div", "label": "Common dividends paid", "col": 1, "kind": "key"},
       {"id": "ret", "label": "Kept in the business (retained)", "col": 1, "kind": "profit"}],
     "links": [["ni","bb",X['bb']],["ni","div",X['div']],["ni","ret",retained]],
     "note": f"Net income 10,833; share repurchases 5,311 (statement of shareholders' equity); common dividends paid 2,271 (cash flow statement). Retained = 10,833 − 5,311 − 2,271 = {retained:,} (derived; ignores $58M of preferred dividends and other equity changes). The 10-K says buybacks plus dividends were $7.6B, about 71% of net income available to common shareholders. A bank's cash flow is mostly loans and deposits, so cash flow is not shown. [[10k]]"},
    {"type": "stats", "items": [
       ["Pre-tax margin", P(X['pt'],X['rev']), "13,795 ÷ 72,229 (derived) [[10k]]"],
       ["Effective tax rate", P(X['tax'],X['pt']), "2,962 ÷ 13,795 (derived) [[10k]]"],
       ["Discount revenue rate", "2.24%", "Share of billed business; 2.29% in 2023 [[10k]]"],
       ["Credit loss provisions", B(X['prov']), "Money set aside for bad loans and charge-offs [[10k]]"]]}
  ]},
  {"id": "employees", "title": "Per employee", "lede": "About 76,800 employees at year-end: about 25,900 in the US and 50,900 elsewhere. [[10k]]", "blocks": [
    {"type": "stats", "items": [
       ["Revenue per employee", K(X['rev'],X['emp']), "72,229M ÷ 76,800 [[10k]]"],
       ["Profit per employee", K(X['ni'],X['emp']), "Net income ÷ employees [[10k]]"],
       ["Pre-tax income per employee", K(X['pt'],X['emp']), "[[10k]]"],
       ["Salaries & benefits per employee", K(X['sal'],X['emp']), "9,016M ÷ 76,800 (derived) [[10k]]"],
       ["Avg. hourly wage", "Not disclosed", "The 10-K gives headcount only, no pay data [[10k]]"]]}
  ]},
  {"id": "geography", "title": "Where the money comes from", "lede": "American Express reports four business segments and revenue by region. Regional figures include management allocations. It does not disclose revenue by US state.", "blocks": [
    {"type": "bars", "title": "Revenue by source, 2025", "unit": "usd", "items": [
       ["Discount revenue", V(X['disc'])], ["Net interest income", V(X['nii'])], ["Net card fees", V(X['fees'])], ["Service fees & other", V(X['svc'])]], "src": ["10k"], "note": "Net interest income = interest income 25.6B − interest expense 8.2B. The four lines add to 72,229, the 10-K's total revenues net of interest expense. [[10k]]"},
    {"type": "bars", "title": "Revenue by region, 2025", "unit": "usd", "items": [
       ["United States", V(56015)], ["EMEA", V(7073)], ["APAC", V(5218)], ["Latin America, Canada & Caribbean", V(4194)]], "src": ["10k"],
     "note": "Excludes −$271M unallocated. Regions are based in part on internal allocations that involve management's judgment. [[10k]]"},
    {"type": "table", "title": "Segments, 2025", "cols": ["Segment", "Revenue (net)", "Pre-tax income"], "align": "lrr",
     "rows": [["U.S. Consumer Services", "$34.8B", "$6.8B"], ["Commercial Services", "$16.9B", "$3.7B"], ["International Card Services", "$13.0B", "$1.6B"],
              ["Global Merchant & Network Services", "$7.8B", "$4.0B"], ["Corporate & other", "−$0.3B", "−$2.3B"], ["Total", "$72.2B", "$13.8B"]], "src": ["10k"]}
  ]},
  {"id": "decisions", "title": "The decisions behind the numbers", "blocks": [
    {"type": "cards", "items": [
      {"kicker": "Premium fees", "big": "$10.0B", "title": "net card fees, up 18%",
       "text": "Net card fees were $7.3B in 2023, $8.4B in 2024 and $10.0B in 2025. The average fee per card rose from $92 to $117 over two years, as more members move to fee-paying premium cards. The 10-K credits new Card Member acquisition and product refreshes.", "src": ["10k"]},
      {"kicker": "Rewards", "big": P(30923,X['rev'],0), "title": "of revenue goes to rewards, benefits and merchant incentives",
       "text": "Card Member rewards 18.4B + business development 6.5B + Card Member services 6.1B = $30.9B, or 43% of net revenue (derived). That is the biggest cost, ahead of salaries ($9.0B) and marketing ($6.3B). Card Member services rose 27% on the new US Platinum benefits.", "src": ["10k"]},
      {"kicker": "Merchant fees", "big": "2.24%", "title": "average discount rate, falling slowly",
       "text": "Discount revenue was 2.24% of billed business in 2025, 2.27% in 2024 and 2.29% in 2023. Billed business grew 8% to $1,669.8B. The 10-K cites shifts in geographic and merchant spend mix.", "src": ["10k"]},
      {"kicker": "Interest", "big": "$17.4B", "title": "net interest income, up 12%",
       "text": "Interest income $25.6B less interest expense $8.2B. Growth came from revolving loan balances, partly offset by lower rates. Customer deposits rose $13.0B in the year.", "src": ["10k"]},
      {"kicker": "Capital return", "big": "$7.6B", "title": "returned to shareholders",
       "text": "$5.3B of buybacks (16.8 million shares at an average $312.87) and $2.3B of dividends, about 71% of net income to common, per the 10-K. The quarterly dividend goes from $0.82 to $0.95 starting with the Q1 2026 declaration.", "src": ["10k"]}
    ]}
  ]},
  {"id": "timeline", "title": "Five years of results", "lede": "Revenue net of interest expense and net income by year, from the 10-Ks. Buybacks here are cash paid for repurchases and other (cash flow statement), which includes shares withheld for taxes, so they differ slightly from the $5.3B of repurchases above.", "blocks": [
    {"type": "timeline", "items": [
      tl("2021", "Revenue $42.4B, net income $8.1B. Buybacks $7.7B, dividends $1.4B.", ["facts"]),
      tl("2022", "Revenue $52.9B, net income $7.5B. Buybacks $3.5B, dividends $1.6B.", ["facts"]),
      tl("2023", "Revenue $60.5B, net income $8.4B. Buybacks $3.7B, dividends $1.8B.", ["10k"]),
      tl("2024", "Revenue $65.9B, net income $10.1B. Buybacks $6.0B, dividends $2.0B.", ["10k"]),
      tl("2025", "Revenue $72.2B (up 10%), net income $10.8B. Buybacks $5.8B, dividends $2.3B.", ["10k"])]}
  ]},
 ]}
write('american-express', amex)
