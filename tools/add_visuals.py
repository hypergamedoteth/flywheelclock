#!/usr/bin/env python3
"""Adds the three visuals to the four company data files (idempotent; run after the seed_* scripts).
 1. 'answer' section: plain-English answer + paired bars (revenue vs profit by segment)
 2. 'flow' section: income-statement Sankey becomes the live-flow Sankey and extends from net income to dividends / buybacks / retained
 3. 'loop' section: flywheel loop with filed numbers
All figures are US$ millions from each company's 10-K (see the notes in each block)."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def load(s): return json.load(open(f"{ROOT}/data/{s}.json", encoding="utf-8"))
def save(s, e): open(f"{ROOT}/data/{s}.json", "w", encoding="utf-8").write(json.dumps(e, indent=1, ensure_ascii=False) + "\n")
def pct(a, b, d=1): return f"{a / b * 100:.{d}f}%"

def put(e, sec, before=None):
    e["sections"] = [s for s in e["sections"] if s["id"] != sec["id"]]
    e["sections"].append(sec)

def live_sankey(e, secs, text, extra_nodes, extra_links, derived, note_add=""):
    flow = next(s for s in e["sections"] if s["id"] == "flow")
    sk = flow["blocks"][0]
    sk.update(live=True, id="sk", period_seconds=secs, period_text=text, derived=derived)
    ids = {n["id"] for n in sk["nodes"]}
    if "ret" not in ids and "retained" not in ids:
        sk["nodes"] += extra_nodes; sk["links"] += extra_links
    if note_add and note_add not in sk["note"]: sk["note"] += " " + note_add
    # the old second sankey for AmEx duplicated the payout split
    flow["blocks"] = [b for i, b in enumerate(flow["blocks"]) if not (e["slug"] == "american-express" and b["type"] == "sankey" and i > 0)]

# ------------------------------------------------------------------ Costco
e = load("costco")
put(e, {"id": "answer", "title": "The short answer", "lede":
  "Costco earns money in two ways: a thin markup on goods, and membership fees. In fiscal 2026 membership fees were **{f}** of revenue but about **{h}** of operating income (derived, math below). [[10k]]".format(f=pct(5907, 303154), h=pct(5907, 11685, 0)),
  "blocks": [
  {"type": "pairs", "groups": [
    {"title": "Where revenue comes from", "sub": "Total revenue FY2026, as reported on the income statement.", "total": 303154, "src": ["10k"],
     "items": [{"label": "Merchandise (net sales)", "value": 297247, "key": "m"}, {"label": "Membership fees", "value": 5907, "key": "f"}]},
    {"title": "Where operating profit comes from", "sub": "Derived (†): Costco reports operating income by geography only, not by fees vs. merchandise.", "total": 11685, "total_label": "Operating income", "src": ["10k"],
     "items": [{"label": "Membership fees †", "value": 5907, "key": "f"}, {"label": "Merchandise, after all costs †", "value": 5778, "key": "m"}]}],
   "callout": "Membership fees: **1.9%** of revenue, **50.6%** of operating income (5,907 ÷ 11,685, derived). A year earlier: fees 5,323 of 10,383 operating income = 51.3% (derived).",
   "note": "† Derived. Costco's 10-K reports membership fees as a revenue line but reports operating income only by geographic segment (below). This view assumes every fee dollar falls to operating income (no cost is allocated to fees) and the rest, 11,685 − 5,907 = 5,778, is what merchandise earned after merchandise costs and SG&A. US$ millions. [[10k]]"},
  {"type": "pairs", "groups": [
    {"title": "Revenue by reported segment", "sub": "The three segments Costco reports, FY2026.", "total": 303154, "src": ["10k"],
     "items": [{"label": "United States", "value": 219823, "key": "us"}, {"label": "Canada", "value": 40561, "key": "ca"}, {"label": "Other International", "value": 42770, "key": "oi"}]},
    {"title": "Operating income by reported segment", "sub": "Segment operating income as filed.", "total": 11685, "total_label": "Operating income", "src": ["10k"],
     "items": [{"label": "United States", "value": 7647, "key": "us"}, {"label": "Canada", "value": 2107, "key": "ca"}, {"label": "Other International", "value": 1931, "key": "oi"}]}],
   "note": "Operating margin: US 3.5%, Canada 5.2%, Other International 4.5% (derived). [[10k]]"}]})
live_sankey(e, 31449600,
  "Fiscal-year total ÷ seconds in the fiscal year. Costco's FY2026 was 52 weeks = 364 days = 31,449,600 seconds (not 365 days). Each counter shows that per-second rate × seconds since Jan 1 in your time zone.",
  [{"id": "div", "label": "Dividends paid", "col": 5, "kind": "key"}, {"id": "bb", "label": "Share buybacks", "col": 5, "kind": "key"}, {"id": "ret", "label": "Kept in the business †", "col": 5, "kind": "profit"}],
  [["ni", "div", 2458], ["ni", "bb", 848], ["ni", "ret", 5920]], ["ret"],
  "Net income 9,226 → dividends 2,458 + buybacks 848 (cash flow statement) + kept in the business 5,920 (9,226 − 2,458 − 848, derived). No special dividend in FY2026. [[10k]]")
put(e, {"id": "loop", "title": "The flywheel", "lede": "Costco's own description of how the model feeds itself, with the filed numbers on each step. The 10-K states these links as its business model and beliefs, not as measured cause and effect.",
  "blocks": [{"type": "loop", "title": "Costco's loop, FY2026", "steps": [
   {"title": "Low prices", "figure": "11.09% gross margin", "edge": "10.1% sales growth", "text": "Costco says offering low prices on a limited selection of products \"will produce high sales volumes and rapid inventory turnover\". Gross margin was 32,968 on net sales of 297,247 = 11.09%.", "src": ["10k"]},
   {"title": "High volume", "figure": "$297.2B net sales", "edge": "$264.3B bought", "text": "Net sales rose from 269,912 to 297,247 (+10.1%, derived).", "src": ["10k"]},
   {"title": "Lower costs", "figure": "SG&A 9.15% of sales", "edge": "75.2% Exec. sales", "text": "Executive members were about 75.2% of worldwide net sales. The 10-K says volume purchasing, efficient distribution and no-frills warehouses \"enable us to operate profitably at significantly lower gross margins\" than most retailers. SG&A was 27,190 = 9.15% of net sales, versus 9.25% in FY2025 (24,966 ÷ 269,912, both derived).", "src": ["10k"]},
   {"title": "Members renew", "figure": "92.3% US & Canada", "edge": "$5.9B fees", "text": "Membership fees were 5,907 (+11%). Renewal rates were 92.3% in the U.S. and Canada and 89.8% worldwide. The 10-K says that sustaining \"high renewal rates materially influences our profitability\". It does not say fees fund lower prices.", "src": ["10k"]}],
   "note": "Renewal rate is Costco's trailing calculation (renewals 7 to 18 months before the reporting date). Derived figures are marked. [[10k]]"}]})
save("costco", e)

# ------------------------------------------------------------------ Apple
e = load("apple")
prod = 209586 + 33708 + 28023 + 35686
put(e, {"id": "answer", "title": "The short answer", "lede":
  "Apple sells devices, and sells services that run on them. In fiscal 2025 Services were **{r}** of net sales but **{g}** of gross margin, because Services earned a 75.4% margin against 36.8% on products (derived). [[10k]]".format(r=pct(109158, 416161), g=pct(82314, 195201)),
  "blocks": [{"type": "pairs", "groups": [
    {"title": "Where revenue comes from", "sub": "Net sales FY2025: products vs. Services.", "total": 416161, "src": ["10k"],
     "items": [{"label": "Products (iPhone, Mac, iPad, Wearables)", "value": prod, "key": "p"}, {"label": "Services", "value": 109158, "key": "s"}]},
    {"title": "Where gross profit comes from", "sub": "Gross margin FY2025 as filed. Apple reports operating income only by geography, so gross margin is the product/services profit view.", "total": 195201, "total_label": "Gross margin", "src": ["10k"],
     "items": [{"label": "Products", "value": 112887, "key": "p"}, {"label": "Services", "value": 82314, "key": "s"}]}],
   "callout": "Services: **26.2%** of net sales, **42.2%** of gross margin (derived). Gross margin percentage: Services 75.4%, Products 36.8% (as filed).",
   "note": "Apple's 10-K does not allocate R&D (34,550) or SG&A (27,601) to products or Services, so operating profit by product line is not reported and not shown. Reported segment operating income by region is in the Geography section. US$ millions. [[10k]]"}]})
live_sankey(e, 31449600,
  "Fiscal-year total ÷ seconds in the fiscal year. Apple's FY2025 was 52 weeks = 364 days = 31,449,600 seconds (not 365 days). Each counter shows that per-second rate × seconds since Jan 1 in your time zone.",
  [{"id": "div", "label": "Dividends paid", "col": 5, "kind": "key"}, {"id": "bb", "label": "Share buybacks", "col": 5, "kind": "key"}, {"id": "ret", "label": "Left after payouts †", "col": 5, "kind": "profit"}],
  [["ni", "div", 15421], ["ni", "bb", 90711], ["ni", "ret", 5878]], ["ret"],
  "Net income 112,010 → dividends 15,421 + buybacks 90,711 (cash flow statement) + left after payouts 5,878 (112,010 − 15,421 − 90,711, derived). [[10k]]")
put(e, {"id": "loop", "title": "The flywheel", "lede": "How Apple's filed numbers connect hardware, Services and what the money is used for. Apple's 10-K does not report active devices or say Services growth comes from its installed base, so this loop shows the filed dollars and the one link the company states itself.",
  "blocks": [{"type": "loop", "title": "Apple's loop, FY2025", "steps": [
   {"title": "Devices sold", "figure": "$307.0B products", "edge": "App Store · cloud · ads", "text": "iPhone 209,586, Mac 33,708, iPad 28,023, Wearables/Home/Accessories 35,686 = 307,003 (derived). Products gross margin was 36.8%.", "src": ["10k"]},
   {"title": "Services on them", "figure": "$109.2B (+14%)", "edge": "75.4% margin", "text": "Services (App Store, advertising, cloud services, AppleCare, payments and more) grew 14%, \"primarily due to higher net sales from advertising, the App Store and cloud services\". Apple also says it believes \"decisions by customers to purchase its hardware products depend in part on the availability of third-party software applications and services\".", "src": ["10k"]},
   {"title": "High-margin profit", "figure": "$82.3B services GM", "edge": "$195.2B gross margin", "text": "Services gross margin 82,314 of total 195,201 = 42.2% (derived), at 75.4% against 36.8% for products.", "src": ["10k"]},
   {"title": "Reinvest & return", "figure": "$106.1B returned", "edge": "R&D $34.6B", "text": "R&D 34,550 (+10%). Dividends 15,421 plus buybacks 90,711 returned 106,132 (derived). The 10-K says gross margins \"will be subject to volatility and downward pressure\".", "src": ["10k"]}],
   "note": "Buybacks on a cash basis; the MD&A says $89.3B of shares repurchased. [[10k]]"}]})
save("apple", e)

# ------------------------------------------------------------------ Amazon
e = load("amazon")
put(e, {"id": "answer", "title": "The short answer", "lede":
  "Amazon is a store and a cloud company in one filing. In 2025 AWS was **{r}** of sales but **{o}** of operating income (derived). North America and International retail made the rest. [[10k]]".format(r=pct(128725, 716924), o=pct(45606, 79975)),
  "blocks": [{"type": "pairs", "groups": [
    {"title": "Where revenue comes from", "sub": "Net sales 2025 by reported segment.", "total": 716924, "src": ["10k"],
     "items": [{"label": "North America", "value": 426305, "key": "na"}, {"label": "International", "value": 161894, "key": "in"}, {"label": "AWS", "value": 128725, "key": "aws"}]},
    {"title": "Where operating profit comes from", "sub": "Segment operating income 2025 as filed.", "total": 79975, "total_label": "Operating income", "src": ["10k"],
     "items": [{"label": "North America", "value": 29619, "key": "na"}, {"label": "International", "value": 4750, "key": "in"}, {"label": "AWS", "value": 45606, "key": "aws"}]}],
   "callout": "AWS: **18.0%** of sales, **57.0%** of operating income (derived). Operating margin: AWS 35.4%, North America 6.9%, International 2.9% (derived).",
   "note": "US$ millions. Segment operating income is reported after allocated costs as in the 10-K segment note. [[10k]]"}]})
live_sankey(e, 31536000,
  "Fiscal-year total ÷ seconds in the year. Amazon's fiscal year is the calendar year 2025 = 365 days = 31,536,000 seconds. Each counter shows that per-second rate × seconds since Jan 1 in your time zone.",
  [{"id": "ret", "label": "Kept in the business †", "col": 5, "kind": "profit"}],
  [["ni", "ret", 77670]], ["ret"],
  "Amazon paid no dividends and made no buybacks in 2025, so all 77,670 of net income stays in the business (derived). [[10k]]")
put(e, {"id": "loop", "title": "The flywheel", "lede": "Amazon's own description of its loop: customer experience drives sales, scale lowers costs per unit, cash is reinvested. Each step cites the 10-K. These are Amazon's stated aims and results, not measured cause and effect.",
  "blocks": [{"type": "loop", "title": "Amazon's loop, 2025", "steps": [
   {"title": "Price, selection, speed", "figure": "Sales +12%", "edge": "more unit sales", "text": "Net sales rose to 716,924 from 637,959 (+12%). The 10-K says increased unit sales \"were driven largely by our continued focus on price, selection, and convenience for our customers, including from our fast shipping offers\".", "src": ["10k"]},
   {"title": "Sellers, ads, Prime", "figure": "3P $172B · Ads $69B", "edge": "Prime $49.6B", "text": "Sales growth \"primarily reflects increased unit sales, including sales by third-party sellers, advertising sales, and subscription services\": seller services 172,162, advertising 68,635, subscriptions (including Prime) 49,619.", "src": ["10k"]},
   {"title": "Lower cost per unit", "figure": "Op. margin 11.2%", "edge": "AWS 57% of profit", "text": "To \"decrease our variable costs on a per unit basis and enable us to lower prices\", Amazon says it seeks to increase direct sourcing, increase supplier discounts and reduce defects. Operating income was 79,975 (11.2% of sales, derived), of which AWS earned 45,606 (57%, derived).", "src": ["10k"]},
   {"title": "Cash reinvested", "figure": "Capex $131.8B", "edge": "customer experience", "text": "Operating cash flow was 139,514 and purchases of property and equipment 131,819. The 10-K says operating income is partly offset by \"investments we make in longer-term strategic initiatives, including capital expenditures focused on improving the customer experience\".", "src": ["10k"]}],
   "note": "Capex covers the whole company, including AWS data centers; the 10-K does not split it by purpose in this sentence. [[10k]]"}]})
save("amazon", e)

# ------------------------------------------------------------------ American Express
e = load("american-express")
put(e, {"id": "answer", "title": "The short answer", "lede":
  "American Express earns **{d}** of its revenue from fees merchants pay when cards are used (discount revenue), **{n}** from interest on balances (net of its own interest cost) and **{c}** from annual card fees (derived). [[10k]]".format(d=pct(37401, 72229, 0), n=pct(17364, 72229, 0), c=pct(9993, 72229, 0)),
  "blocks": [{"type": "pairs", "groups": [
    {"title": "Where revenue comes from", "sub": "Total revenues net of interest expense 2025 by reported segment.", "total": 72229, "total_label": "Total revenue (net)", "src": ["10k"],
     "items": [{"label": "U.S. Consumer Services", "value": 34814, "key": "us"}, {"label": "Commercial Services", "value": 16926, "key": "cs"}, {"label": "International Card Services", "value": 13000, "key": "ics"}, {"label": "Global Merchant & Network Services", "value": 7759, "key": "gm"}, {"label": "Corporate & other", "value": -270, "key": "co"}]},
    {"title": "Where pre-tax profit comes from", "sub": "Pretax income 2025 by segment, the measure Amex reports for each segment. Shares are of the four operating segments (16,049).", "total": 13795, "total_label": "Pretax income", "src": ["10k"],
     "items": [{"label": "U.S. Consumer Services", "value": 6810, "key": "us"}, {"label": "Commercial Services", "value": 3668, "key": "cs"}, {"label": "International Card Services", "value": 1603, "key": "ics"}, {"label": "Global Merchant & Network Services", "value": 3968, "key": "gm"}, {"label": "Corporate & other", "value": -2254, "key": "co"}]}],
   "callout": "Global Merchant & Network Services: **10.7%** of segment revenue but **24.7%** of segment pretax income (derived, shares of the four operating segments). International Card Services: 18.0% of revenue, 10.0% of pretax income.",
   "note": "American Express reports segment pretax income, not operating income. Corporate & other (−2,254 pretax, −270 revenue) is not drawn; it brings the four segments' 16,049 down to the consolidated 13,795. US$ millions. [[10k]]"}]})
live_sankey(e, 31536000,
  "Fiscal-year total ÷ seconds in the year. American Express's fiscal year is the calendar year 2025 = 365 days = 31,536,000 seconds. Each counter shows that per-second rate × seconds since Jan 1 in your time zone.",
  [{"id": "bb", "label": "Share buybacks", "col": 5, "kind": "key"}, {"id": "div", "label": "Common dividends paid", "col": 5, "kind": "key"}, {"id": "ret", "label": "Kept in the business †", "col": 5, "kind": "profit"}],
  [["ni", "bb", 5311], ["ni", "div", 2271], ["ni", "ret", 3251]], ["ret", "gross"],
  "Net income 10,833 → buybacks 5,311 (statement of shareholders' equity) + common dividends 2,271 (cash flow statement) + kept 3,251 (10,833 − 5,311 − 2,271, derived; ignores $58M of preferred dividends and other equity changes). The 10-K says buybacks plus dividends were $7.6B, about 71% of net income available to common shareholders. A bank's cash flow is mostly loans and deposits, so cash flow is not shown. [[10k]]")
put(e, {"id": "loop", "title": "The flywheel", "lede": "American Express's own description of its model: card spend earns merchant fees, part of which goes back to Card Members as rewards and services to drive more spending. Each step cites the 10-K. These are stated aims and filed results, not measured cause and effect.",
  "blocks": [{"type": "loop", "title": "American Express's loop, 2025", "steps": [
   {"title": "Card spend", "figure": "$1,669.8B billed", "edge": "2.24% discount rate", "text": "Billed business was 1,669.8 billion (+8%). The 10-K says the business model focuses on \"generating revenues primarily by driving spending on our cards and secondarily through finance charges and fees\".", "src": ["10k"]},
   {"title": "Discount revenue", "figure": "$37.4B", "edge": "$18.4B rewards", "text": "Discount revenue was 37,401, equal to 2.24% of billed business (2.27% in 2024), the largest of the four revenue lines.", "src": ["10k"]},
   {"title": "Rewards & services", "figure": "Rewards $18.4B", "edge": "card fees $10.0B", "text": "Card Member rewards 18,409 and Card Member services 6,057. Amex says it offers \"incentives to drive spending on our various card products and increase customer engagement, including our Membership Rewards and Amex Offers programs\".", "src": ["10k"]},
   {"title": "More cards, more spend", "figure": "86.6M cards (+4%)", "edge": "12.5M new cards", "text": "Proprietary cards-in-force 86.6 million (+4%), average proprietary basic Card Member spending $25,453 (+3%), net card fees 9,993 (average fee per card $117, +14%).", "src": ["10k"]}],
   "note": "Net interest income (17,364) and service fees (7,471) also add to revenue but are outside this spend loop. [[10k]]"}]})
for n in next(s for s in e["sections"] if s["id"] == "flow")["blocks"][0]["nodes"]:
    n["label"] = {"gross": "Gross revenue †", "net": "Net revenue"}.get(n["id"], n["label"])
save("american-express", e)

# ------------------------------------------------------------------ Gold holder waffle
e = load("gold")
own = next(x for x in e["sections"] if x["id"] == "owners")
own["blocks"] = [b for b in own["blocks"] if b["type"] != "waffle"]
own["blocks"].insert(1, {"type": "waffle", "title": "Every tonne of gold ever mined, by holder", "unit": "tonnes", "dec": 1, "cell": 1000, "cell_label": "1,000 tonnes (1,000,000 kg)", "cols": 24,
  "total_label": "Approx. gold ever mined",
  "items": [{"label": "Central banks & governments (79 IMF reporters)", "value": 31221.9, "src": ["irfcl"]}, {"label": "IMF", "value": 2814.1, "src": ["imfgold"]},
            {"label": "Largest US gold ETFs (GLD, IAU, GLDM)", "value": 1739.55, "src": ["gld", "iau", "gldm"]}, {"label": "Tether (disclosed company)", "value": 168.2, "src": ["tether"]},
            {"label": "Privately held, owner not public (jewelry, bars, coins)", "value": 180046.2, "est": True, "est_label": "derived estimate", "color": "#3a4252", "src": []}],
  "note": "The first four holders are published figures. The hatched block is not reported anywhere: it is the USGS-based estimate of all gold ever mined (215,990 t) minus the named holders, so it carries the uncertainty of that estimate. The IMF, ETF and Tether blocks are small next to one square: Tether rounds to zero squares, so use the table for exact tonnes."})
save("gold", e)
print("ok")
