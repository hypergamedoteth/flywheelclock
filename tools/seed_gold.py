"""Regenerate data/gold.json. Free / public-domain data only (USGS, IMF, issuers' own disclosures).
No World Gold Council figures. Inputs: USGS DS140 + MCS 2025/2026 (raw/), IMF IRFCL pull (tools/irfcl_gold_clean.json),
issuer pages (GLD/GLDM archive xlsx from spdrgoldshares.com, IAU page on ishares.com), Tether reports, and gold.md.
Re-run:  python3 tools/seed_gold.py && python3 build.py"""
import json, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OZ_PER_T = 32150.7466

src = {
 "mcs26": ["USGS Mineral Commodity Summaries 2026: Gold (public domain)", "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-gold.pdf"],
 "mcs25": ["USGS Mineral Commodity Summaries 2025: Gold (public domain)", "https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-gold.pdf"],
 "ds140": ["USGS Data Series 140, Gold historical statistics (world production 1900–2022; public domain)", "https://www.usgs.gov/media/files/gold-historical-statistics-data-series-140"],
 "usgsfaq": ["USGS FAQ: How much gold has been found in the world?", "https://www.usgs.gov/faqs/how-much-gold-has-been-found-world"],
 "irfcl": ["International Monetary Fund, International Reserves and Foreign Currency Liquidity (IRFCL), official reserve assets, gold volume. Accessed Oct 26, 2026", "https://data.imf.org/en/datasets/IMF.STA:IRFCL"],
 "imfgold": ["IMF factsheet: Gold in the IMF", "https://www.imf.org/en/about/factsheets/sheets/2022/gold-in-the-imf"],
 "gld": ["SPDR Gold Shares (GLD): trust holdings, historical archive, Oct 23, 2026", "https://www.spdrgoldshares.com/usa/gld/"],
 "gldm": ["SPDR Gold MiniShares (GLDM): trust holdings, historical archive, Oct 23, 2026", "https://www.spdrgoldshares.com/usa/gldm/"],
 "iau": ["iShares Gold Trust (IAU): tonnes in trust, Oct 23, 2026", "https://www.ishares.com/us/products/239561/ishares-gold-trust-fund"],
 "tether": ["Tether: XAU₮ reserve reports and USDT reserve attestation (BDO), Jun 30, 2026", "https://gold.tether.to/reports"],
 "nyfed": ["Federal Reserve Bank of New York: The Gold Vault", "https://www.newyorkfed.org/aboutthefed/goldvault.html"],
 "boe": ["Bank of England: Gold", "https://www.bankofengland.co.uk/gold"],
 "lbma_vault": ["LBMA: London vault holdings data", "https://www.lbma.org.uk/prices-and-data/london-vault-data"],
 "treasury": ["US Treasury: Status Report of U.S. Government Gold Reserve, Sep 2026", "https://fiscaldata.treasury.gov/datasets/status-report-government-gold-reserve/"],
 "zeit": ["Die Zeit, Jan 2026, on where the Bundesbank stores its gold", None],
 "barrick": ["Barrick: Nevada Gold Mines", "https://www.barrick.com/"],
 "mining": ["Mining.com: world's largest gold mines", "https://www.mining.com/"],
 "polyus": ["Polyus: operations", "https://polyus.com/en/"],
 "cme": ["CME Group: record annual ADV in 2025 (press release)", "https://investor.cmegroup.com/news-releases/news-release-details/cme-group-reports-record-annual-adv-281-million-contracts-2025-6"],
 "lbma_trade": ["LBMA: daily trade reporting data", "https://www.lbma.org.uk/prices-and-data/lbma-daily-trade-reporting-data"],
 "usmint": ["US Mint: Fort Knox Bullion Depository", "https://www.usmint.gov/about/tours-and-locations/fort-knox"],
 "frbhist": ["Federal Reserve History", "https://www.federalreservehistory.org/"],
 "lbma_q": ["LBMA quarterly market reports (Q1 and Q2 2026)", "https://www.lbma.org.uk/"],
 "ucsb": ["The American Presidency Project (UCSB): Executive Order 6102", "https://www.presidency.ucsb.edu/"],
 "ishares_iau": ["iShares Gold Trust fact sheet", "https://www.ishares.com/us/products/239561/ishares-gold-trust-fund"],
 "wiki": ["Wikipedia (secondary source)", "https://en.wikipedia.org/"],
 "goldfields": ["Gold Fields: history of the Carlin Trend and Grasberg", "https://www.goldfields.com/"],
}

NAMES = dict(USA="United States",DEU="Germany",ITA="Italy",FRA="France",CHN="China",RUS="Russia",CHE="Switzerland",IND="India",JPN="Japan",TUR="Türkiye",POL="Poland",NLD="Netherlands",EZB="European Central Bank",PRT="Portugal",KAZ="Kazakhstan",SAU="Saudi Arabia",GBR="United Kingdom",ESP="Spain",AUT="Austria",THA="Thailand",BEL="Belgium",SGP="Singapore",BRA="Brazil",PHL="Philippines",EGY="Egypt",SWE="Sweden",ZAF="South Africa",MEX="Mexico",GRC="Greece",HUN="Hungary",KOR="South Korea",ROU="Romania",CZE="Czech Republic",IDN="Indonesia",AUS="Australia",JOR="Jordan",DNK="Denmark",ARG="Argentina",KHM="Cambodia",SRB="Serbia",BLR="Belarus",MYS="Malaysia",FIN="Finland",BGR="Bulgaria",PER="Peru",UKR="Ukraine",ECU="Ecuador",MAR="Morocco",GTM="Guatemala",CYP="Cyprus",MUS="Mauritius",IRL="Ireland",PRY="Paraguay",MNG="Mongolia",GEO="Georgia",MKD="North Macedonia",LVA="Latvia",LTU="Lithuania",COL="Colombia",SVN="Slovenia",ALB="Albania",LUX="Luxembourg",SLV="El Salvador",HKG="Hong Kong SAR",ISL="Iceland",LKA="Sri Lanka",URY="Uruguay",HND="Honduras",MLT="Malta",DOM="Dominican Republic",EST="Estonia",CHL="Chile",MDA="Moldova",ARM="Armenia",CRI="Costa Rica",JAM="Jamaica",NIC="Nicaragua",NOR="Norway",WBG="West Bank and Gaza")
MON = {f"M{m:02d}": n for m, n in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), 1)}
cb = json.load(open(os.path.join(HERE, 'tools/irfcl_gold_clean.json')))
cb_total = round(sum(x['tonnes'] for x in cb), 1)

# ---- total ever mined (USGS only)
FAQ_BASE = 187000            # USGS FAQ "historically produced"; paired with 57,000 t reserves = MCS 2017 (end-2016 basis, inferred)
SINCE = {2017: 3260, 2018: 3310, 2019: 3260, 2020: 3050, 2021: 3120, 2022: 3160, 2023: 3250, 2024: 3280, 2025: 3300}
since_sum = sum(SINCE.values())            # 28,990
TOTAL = FAQ_BASE + since_sum               # 215,990
DOC_1900_2025 = 185173                     # sum of DS140 world production 1900–2022 + MCS 2023–2025

IMF_T = 2814.1
etfs = [["SPDR Gold Shares (GLD)", 1041.65, "Oct 23, 2026", "gld"], ["iShares Gold Trust (IAU)", 463.05, "Oct 23, 2026", "iau"], ["SPDR Gold MiniShares (GLDM)", 234.85, "Oct 23, 2026", "gldm"]]
etf_t = round(sum(e[1] for e in etfs), 2)
TETHER = 168.2  # 146.19 USDT reserves + 22.01 XAUT, Jun 30, 2026
named = cb_total + IMF_T + etf_t + TETHER
private = round(TOTAL - named, 1)
pct = lambda t: f"{t / TOTAL * 100:.1f}%"
fmt = lambda t: f"{t:,.1f}"

holders = [
  {"label": f"Central banks & governments ({len(cb)} IMF reporters)", "t": cb_total, "kind": "official", "src": ["irfcl"]},
  {"label": "IMF", "t": IMF_T, "kind": "official2", "src": ["imfgold"]},
  {"label": "Largest US gold ETFs (GLD, IAU, GLDM)", "t": etf_t, "kind": "etf", "src": ["gld", "iau", "gldm"]},
  {"label": "Tether (disclosed company)", "t": TETHER, "kind": "co", "src": ["tether"]},
  {"label": "Privately held, owner not public (jewelry, bars, coins)", "t": private, "kind": "private", "src": []},
]

cb_rows = []
for i, x in enumerate(cb[:20], 1):
    y, m = x['period'].split('-')
    cb_rows.append([str(i), NAMES.get(x['code'], x['code']), fmt(x['tonnes']), f"{MON[m]} {y}"])

rate_g = 3300e6
data = {
 "type": "commodity", "slug": "gold", "live": True, "name": "Gold", "symbol": "Au",
 "title": "Where all the gold is: who owns it, where it's stored, and how much is left",
 "description": "About 216,000 tonnes of gold have been mined. See who owns it (central banks, the IMF, ETFs), where it sits, what's left in the ground, and a live mining clock. USGS and IMF data.",
 "tagline": "About 216,000 tonnes mined in all of history. Roughly 1 in 6 has a named owner.",
 "card_stat": {"label": "Mined per second", "value": "~105 g", "note": "USGS 2025 estimate"},
 "as_of": "USGS MCS 2026 (Jan 2026), IMF IRFCL (data to Sep 2026), issuer holdings Oct 23, 2026",
 "sources": src,
 "sections": [
  {"id": "ticker", "title": "Gold, live", "blocks": [
    {"type": "ticker", "period_seconds": 31557600, "period_label": "a year",
     "label": "projected from USGS 2025 annual mine production",
     "counters": [
       {"id": "g", "label": "Gold mined", "annual": rate_g, "unit": "gold", "hero": True},
       {"id": "v", "label": "Value at the USGS 2025 average price ($3,300/oz)", "annual": 3300 * OZ_PER_T * 3300, "unit": "usd"}],
     "note": "3,300 tonnes a year (USGS 2025 estimate) ÷ 31,557,600 seconds ≈ 104.6 grams a second. The dollar line uses USGS's 2025 average price of $3,300/oz (Engelhard quotation), not a live price. [[mcs26]]",
     "facts": [["Mined in 2025", "~3,300 t"], ["Ever mined (approx.)", f"~{TOTAL:,} t"], ["Left in reserves", "~66,000 t"], ["Years at today's pace", "~20"]]}
  ]},
  {"id": "owners", "title": "Where all the gold is", "lede": "Every tonne ever mined, split into owners that are publicly named and everything else.", "blocks": [
    {"type": "stack", "total": TOTAL, "unit": "t",
     "items": [{"label": h["label"], "value": h["t"], "kind": h["kind"], "src": h["src"]} for h in holders],
     "headline": f"Only about {pct(named)} of all gold ever mined has a publicly named owner."},
    {"type": "math", "title": "Approx. gold ever mined (USGS cumulative production)", "lines": [
       f"USGS: about 187,000 t \"historically produced\" (the FAQ pairs this with 57,000 t of reserves, the MCS 2017 figure, so it's read here as through end-2016). [[usgsfaq]]",
       f"+ world mine production 2017–2022: 3,260 + 3,310 + 3,260 + 3,050 + 3,120 + 3,160 = 19,160 t [[ds140]]",
       f"+ 2023–2025: 3,250 + 3,280 + 3,300 = 9,830 t [[mcs25]] [[mcs26]]",
       f"= **~{TOTAL:,} t** approx. gold ever mined",
       f"Cross-check: USGS year-by-year world production 1900–2025 alone sums to {DOC_1900_2025:,} t; the rest (~{TOTAL - DOC_1900_2025:,} t) was mined before 1900."]},
    {"type": "math", "title": "Who owns it (the math)", "lines": [
       f"Central banks & governments: {fmt(cb_total)} t, the sum of the latest monthly gold holdings of {len(cb)} reporters to the IMF (including the ECB). [[irfcl]]",
       f"IMF's own gold: {fmt(IMF_T)} t (90.5M oz). [[imfgold]]",
       f"ETFs: GLD 1,041.65 + IAU 463.05 + GLDM 234.85 = {etf_t:,} t, from each issuer's own published holdings. [[gld]] [[iau]] [[gldm]]",
       "Tether: 146.19 t backing USDT + 22.01 t backing XAU₮ = 168.2 t (Jun 30, 2026). [[tether]]",
       "Disclosed individuals: none. No person's personal bullion holding is publicly verified.",
       f"Privately held, owner not public = {TOTAL:,} − {fmt(named)} = **{private:,.1f} t ({pct(private)})**"],
     "note": "The \"owner not public\" bucket is everything without a named holder: jewelry, private bars and coins, gold in other ETFs and funds, industrial gold, gold lost over history, and any official gold not reported to the IMF. Dates differ by row. Treat all shares as approximate."},
    {"type": "note", "text": "Jewelry is the largest single use of newly consumed gold, according to USGS's 2026 summary. [[mcs26]]"}
  ]},
  {"id": "countries", "title": "Countries and central banks", "lede": f"Official gold reported to the IMF by {len(cb)} central banks and governments: {fmt(cb_total)} t in total. Top 20, latest month reported.", "blocks": [
    {"type": "table", "cols": ["#", "Holder", "Tonnes", "As of"], "align": "llrr", "rows": cb_rows,
     "note": "Source: International Monetary Fund, International Reserves and Foreign Currency Liquidity (IRFCL), gold volume in fine troy ounces ÷ 32,150.75. Brazil's value is reported in thousandths of an ounce and was divided by 1,000; Angola and Kosovo were left out because their units look wrong. Some holders (for example several Gulf states, Uzbekistan, Iraq and Taiwan) don't report gold in IRFCL and aren't counted. [[irfcl]]"},
    {"type": "stats", "items": [["IMF", f"{fmt(IMF_T)} t", "Held at designated depositories in the US, UK, France and India [[imfgold]]"],
                                ["US Treasury (USGS)", "8,130 t", "Valued at the official $42.22/oz [[mcs26]]"]]}
  ]},
  {"id": "etfs", "title": "Funds and companies", "blocks": [
    {"type": "table", "cols": ["Holder", "Tonnes", "As of", "Where"], "align": "lrrl",
     "rows": [["SPDR Gold Shares (GLD)", "1,041.65", "Oct 23, 2026", "HSBC vault (per the trust's bar list) [[gld]]"],
              {"cells": ["iShares Gold Trust (IAU)", "463.05", "Oct 23, 2026", "Custodian JPMorgan (London/NY) [[iau]]"], "verify": True},
              ["SPDR Gold MiniShares (GLDM)", "234.85", "Oct 23, 2026", "[[gldm]]"],
              ["Tether: USDT reserves", "146.19", "Jun 30, 2026", "Swiss vault, location undisclosed [[tether]]"],
              ["Tether Gold (XAU₮)", "22.01", "Jun 30, 2026", "Swiss vault [[tether]]"]],
     "note": "Fund shareholders are the beneficial owners. Brokers report fund positions in SEC 13F filings, but those name the broker, not the end investor, and 13Fs don't cover physical bullion. Billionaire gold positions that show up publicly (e.g. Tudor Investment) are fund positions, not personal metal."}
  ]},
  {"id": "storage", "title": "Where it's physically stored", "blocks": [
    {"type": "table", "title": "The biggest vaults", "cols": ["Vault", "Tonnes", "Whose gold"], "align": "lrl",
     "rows": [["London vaults (all LBMA, incl. Bank of England)", "9,821 (end-Sep 2026)", "Central banks, ETFs, banks [[lbma_vault]]"],
              ["New York Fed, 80 ft below Manhattan", "~6,331 (2024)", "Foreign central banks and the US Treasury; the Fed owns none [[nyfed]]"],
              ["Bank of England", "5,782 (end-Sep 2026)", "Central banks and LBMA members [[boe]]"],
              ["Fort Knox, Kentucky", "4,583 (147.34M oz)", "US Treasury [[treasury]]"],
              ["Swiss vaults (Zurich and others)", "Unknown", "Private clients, funds, Tether. No official total."]]},
    {"type": "table", "title": "Where the two biggest holders keep theirs", "cols": ["Holder", "Location", "Tonnes"], "align": "llr",
     "rows": [["United States", "Fort Knox", "4,583"], ["United States", "West Point", "~1,682"], ["United States", "Denver Mint", "~1,364"], ["United States", "New York Fed (Treasury-owned)", "~416"], ["United States", "Working stock", "~87"],
              ["Germany", "Frankfurt", "1,710"], ["Germany", "New York Fed", "1,236"], ["Germany", "London (Bank of England)", "405"]],
     "note": "US: Treasury gold reserve status report, Sep 2026 (ounces ÷ 32,150.7). [[treasury]] Germany: Die Zeit, Jan 2026. [[zeit]] China, Russia and most Gulf states don't disclose where their gold is kept."},
    {"type": "list", "title": "Disclosed by others", "items": [
       {"text": "IMF gold sits in depositories in New York, London, Paris and Nagpur; the split isn't public. [[imfgold]]"},
       {"text": "Switzerland: about 70% in Switzerland, 20% at the Bank of England and 10% in Canada (SNB statement, 2013).", "verify": True},
       {"text": "France: the 129 t once held in New York was sold and replaced in Europe.", "verify": True},
       {"text": "India: the majority is now held domestically.", "verify": True}]}
  ]},
  {"id": "reserves", "title": "Still in the ground", "lede": "World reserves: about 66,000 t (USGS). At 2025's pace that's about 20 years of mining (66,000 ÷ 3,300, derived). Reserves get revised up as prices rise and new deposits are proven, so this isn't a countdown. [[mcs26]]", "blocks": [
    {"type": "bars", "title": "Reserves by country (tonnes)", "unit": "t", "src": ["mcs26"], "items": [
       ["Australia", 13000], ["Russia", 12000], ["South Africa", 5000], ["Indonesia", 3600], ["China", 3200], ["Canada", 3200], ["United States", 3000], ["Brazil", 2500], ["Kazakhstan", 2300], ["Uzbekistan", 2200], ["Peru", 2200], ["Mexico", 1400], ["Ghana", 1000], ["Other countries", 11000]],
     "note": "Australia's JORC-compliant reserves are 4,500 t. US identified + undiscovered resources: about 33,000 t. [[mcs26]]"},
    {"type": "table", "title": "Major mines and who owns them", "cols": ["Mine", "Country", "Owner(s)", "Size"], "align": "llll",
     "rows": [["Nevada Gold Mines", "USA", "Barrick 61.5% / Newmont 38.5%", "2.70 Moz produced (2024) [[barrick]]"],
              ["Muruntau", "Uzbekistan", "State-owned (NMMC)", "~2.68 Moz a year [[mining]]"],
              ["Grasberg", "Indonesia", "Indonesian state (MIND ID) 51.24% / Freeport 48.76%", "1.86 Moz [[mining]]"],
              {"cells": ["Olimpiada", "Russia", "Polyus (controlled by the Kerimov family's holding)", "1.44 Moz (2024) [[polyus]]"], "verify": True},
              ["Sukhoi Log", "Russia", "Polyus", "40 Moz reserves, not yet producing [[polyus]]"],
              ["South Deep", "South Africa", "Gold Fields", "32.8 Moz reserves (2018) [[mining]]"]]}
  ]},
  {"id": "mining", "title": "Who mines it", "lede": "World mine production: 3,300 t in 2025 (estimate), 3,280 t in 2024. The top five produced 41% of the 2025 total. [[mcs26]]", "blocks": [
    {"type": "bars", "title": "Mine production, 2025 estimate (tonnes)", "unit": "t", "src": ["mcs26"], "items": [
       ["China", 380], ["Russia", 310], ["Australia", 280], ["Canada", 200], ["United States", 160], ["Ghana", 150], ["Mexico", 140], ["Kazakhstan", 130], ["Uzbekistan", 130], ["Peru", 110], ["Indonesia", 90], ["South Africa", 90], ["Brazil", 80], ["Other countries", 1000]],
     "note": "US: Nevada produced about 64% and Alaska 22% of domestic mined gold in 2025. [[mcs26]]"}
  ]},
  {"id": "trading", "title": "How it trades", "blocks": [
    {"type": "stats", "items": [
       ["CME metals futures & options, avg daily volume (2025)", "988k contracts", "A record [[cme]]"],
       ["Micro Gold futures, avg daily volume (2025)", "325k contracts", "[[cme]]"],
       ["Gold options, avg daily volume (2025)", "96k contracts", "[[cme]]"],
       ["GLD shares traded, Oct 23, 2026", "10.1M", "[[gld]]"]]},
    {"type": "note", "text": "Most gold trades over the counter in London. The LBMA publishes weekly 12-week averages of turnover; daily trade data is sold through licensed data vendors, so no OTC total is shown here. The main COMEX gold contract's volume isn't broken out in CME's release. [[lbma_trade]]"}
  ]},
  {"id": "timeline", "title": "Timeline", "lede": "Big events, breakthroughs, people and places.", "blocks": [
    {"type": "timeline", "items": [
      {"date": "c. 4600 BC", "text": "Earliest known worked gold, in the Varna necropolis.", "where": "Varna, Bulgaria", "src": ["wiki"], "verify": True},
      {"date": "c. 600 BC", "text": "First gold and electrum coins.", "where": "Lydia (Türkiye)", "src": ["wiki"], "verify": True},
      {"date": "1848–1855", "text": "California Gold Rush.", "where": "Sutter's Mill, Coloma, CA", "src": ["wiki"]},
      {"date": "1851", "text": "Australian gold rush.", "where": "New South Wales and Victoria", "src": [], "verify": True},
      {"date": "1886", "text": "Gold discovered on the Witwatersrand, the basin that has produced more gold than anywhere else.", "where": "Johannesburg, South Africa", "src": [], "verify": True},
      {"date": "1896–1899", "text": "Klondike Gold Rush.", "where": "Yukon, Canada", "src": [], "verify": True},
      {"date": "1919", "text": "The London Gold Fixing begins.", "where": "N M Rothschild, London", "src": [], "verify": True},
      {"date": "Apr 5, 1933", "text": "Executive Order 6102 bans most private gold ownership in the US.", "where": "Franklin D. Roosevelt", "src": ["ucsb"], "verify": True},
      {"date": "Jan 30, 1934", "text": "Gold Reserve Act resets the price from $20.67 to $35 an ounce.", "where": "", "src": ["frbhist"], "verify": True},
      {"date": "1937", "text": "First gold arrives at Fort Knox.", "where": "Kentucky", "src": ["usmint"]},
      {"date": "Dec 31, 1941", "text": "Fort Knox holdings peak at 649.6M oz.", "where": "", "src": ["usmint"]},
      {"date": "Jul 1944", "text": "Bretton Woods pegs the dollar to gold at $35 and creates the IMF.", "where": "Bretton Woods, NH", "src": ["frbhist"], "verify": True},
      {"date": "1958", "text": "Muruntau discovered; now one of the largest gold mines.", "where": "Uzbekistan", "src": [], "verify": True},
      {"date": "1961–1968", "text": "The London Gold Pool defends the $35 price.", "where": "", "src": [], "verify": True},
      {"date": "1965", "text": "Newmont starts open-pit mining on the newly found Carlin Trend.", "where": "Nevada", "src": ["goldfields"]},
      {"date": "Aug 15, 1971", "text": "Nixon closes the gold window, ending dollar convertibility.", "where": "Richard Nixon", "src": ["frbhist"], "verify": True},
      {"date": "1973", "text": "US official gold price set at $42.22/oz, still the book value today.", "where": "", "src": ["usmint"]},
      {"date": "1973", "text": "The New York Fed vault peaks at more than 12,000 t.", "where": "Manhattan", "src": ["nyfed"]},
      {"date": "Dec 31, 1974", "text": "Private gold ownership becomes legal again in the US.", "where": "Gerald Ford", "src": [], "verify": True},
      {"date": "Jan 21, 1980", "text": "Price spikes to $850/oz.", "where": "", "src": [], "verify": True},
      {"date": "1988", "text": "Grasberg discovered.", "where": "Papua, Indonesia", "src": ["goldfields"]},
      {"date": "1999", "text": "Washington Agreement limits central-bank gold sales; the UK sells at the bottom.", "where": "Gordon Brown", "src": [], "verify": True},
      {"date": "Nov 18, 2004", "text": "GLD launches, making gold trade like a stock.", "where": "NYSE", "src": ["gld"]},
      {"date": "Jan 21, 2005", "text": "iShares Gold Trust (IAU) launches.", "where": "", "src": ["ishares_iau"]},
      {"date": "Sep 2011", "text": "Then-record of about $1,900/oz.", "where": "", "src": [], "verify": True},
      {"date": "2015", "text": "The LBMA Gold Price replaces the London Fix.", "where": "London", "src": ["lbma_q"]},
      {"date": "2017", "text": "Polyus wins the rights to Sukhoi Log (40 Moz of reserves).", "where": "Siberia", "src": ["polyus"]},
      {"date": "2019", "text": "Barrick and Newmont form the Nevada Gold Mines joint venture (61.5% / 38.5%).", "where": "Nevada", "src": ["barrick"]},
      {"date": "Jan 29, 2026", "text": "All-time high of $5,501.70/oz (LBMA AM).", "where": "", "src": ["lbma_q"]},
      {"date": "Jun 2026", "text": "Price falls about 27% from the peak, to about $4,026 (Jun 30 PM).", "where": "", "src": ["lbma_q"]},
      {"date": "Sep 2026", "text": "London vaults hold a record 9,821 t; the Bank of England holds 5,782 t.", "where": "London", "src": ["lbma_vault", "boe"]},
    ], "note": "Long-settled historical entries marked \"verify\" need a primary source (Federal Reserve History, US Mint, LBMA) before launch."}
  ]},
 ]
}
json.dump(data, open(os.path.join(HERE, 'data/gold.json'), 'w'), indent=1, ensure_ascii=False)
print('wrote data/gold.json', 'total', TOTAL, 'cb', cb_total, 'named', round(named, 1), 'private', private, pct(private))
