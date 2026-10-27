#!/usr/bin/env python3
"""Regenerate data/bitcoin.json. Chain data is pulled live from free public APIs (blockchain.info, mempool.space);
holder figures are typed in below from SEC filings and issuer pages (each cited, with its as-of date).
Re-run: python3 tools/seed_bitcoin.py && python3 build.py"""
import json, os, urllib.request, datetime as dt
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read().decode()
height = int(get("https://blockchain.info/q/getblockcount")); circ_sat = int(get("https://blockchain.info/q/totalbc"))
tip = json.loads(get("https://mempool.space/api/block/" + get("https://mempool.space/api/blocks/tip/hash")))
assert tip["height"] == height or abs(tip["height"] - height) < 3
circ = circ_sat / 1e8; tip_ts = tip["timestamp"]; tip_h = tip["height"]
CAP = 20999999.9769           # exact: sum of subsidies in satoshis, 33 eras
def utc(ts): return dt.datetime.fromtimestamp(ts, dt.timezone.utc)
def d(ts): return utc(ts).strftime("%b %-d, %Y")
def dl(ts): return utc(ts).strftime("%b %-d, %Y, %H:%M UTC")
# block timestamps (mempool.space /api/block): genesis, halvings
TS = {0: 1231006505, 210000: 1354116278, 420000: 1468082773, 630000: 1589225023, 840000: 1713571767}
as_of = d(tip_ts)

# subsidy math
eras = []; sub = 50 * 10**8; s = 0
for i in range(33):
    eras.append((i, i * 210000, (i + 1) * 210000 - 1, sub / 1e8, 210000 * sub / 1e8)); s += 210000 * sub; sub //= 2
assert s == 2099999997690000
cur_era = tip_h // 210000; subsidy = 50 / 2 ** cur_era
mined_math = sum(e[4] for e in eras[:cur_era]) + (tip_h - cur_era * 210000 + 1) * subsidy
next_h = (cur_era + 1) * 210000; left = next_h - tip_h - 1
avg = (tip_ts - TS[840000]) / (tip_h - 840000)
est600 = tip_ts + (next_h - tip_h) * 600; estavg = tip_ts + (next_h - tip_h) * avg
per_s = subsidy / 600
not_mined = CAP - circ

src = {
 "bci": ["Blockchain.com public API: total bitcoins in circulation (q/totalbc) and block count (q/getblockcount), read " + as_of + " UTC", "https://www.blockchain.com/explorer/api/q"],
 "mempool": ["mempool.space public API: block height, hash and timestamps (blocks 0, 210,000, 420,000, 630,000, 840,000 and the chain tip)", "https://mempool.space/docs/api/rest"],
 "core": ["Bitcoin Core source: consensus rules (MAX_MONEY 21,000,000 × COIN; subsidy halves every 210,000 blocks)", "https://github.com/bitcoin/bitcoin/blob/master/src/validation.cpp"],
 "ibit": ["iShares Bitcoin Trust ETF (IBIT): holdings table, quantity of bitcoin, as of Oct 26, 2026", "https://www.ishares.com/us/products/333011/ishares-bitcoin-trust-etf"],
 "ibit_q": ["iShares Bitcoin Trust ETF Form 10-Q for the quarter ended June 30, 2026: Schedule of Investments (734,261 bitcoin)", "https://www.sec.gov/Archives/edgar/data/1980994/000143774926026004/bit20260630c_10q.htm"],
 "fbtc": ["Fidelity Wise Origin Bitcoin Fund (FBTC) Form 10-Q, June 30, 2026: bitcoin held by the custodian 174,383", "https://www.sec.gov/Archives/edgar/data/1852317/000119312526337679/ck0001852317-20260630.htm"],
 "gbtc": ["Grayscale Bitcoin Trust ETF (GBTC) Form 10-Q, June 30, 2026: 138,505.75680424 bitcoin", "https://www.sec.gov/Archives/edgar/data/1588489/000158848926000005/gbtc-20260630.htm"],
 "arkb": ["ARK 21Shares Bitcoin ETF (ARKB) Form 10-Q, June 30, 2026: 32,178.2280 bitcoin", "https://www.sec.gov/Archives/edgar/data/1869699/000121390026086191/ea0299118-10q_ark21shares.htm"],
 "bitb": ["Bitwise Bitcoin ETF (BITB) Form 10-Q, June 30, 2026: 36,207.6919 bitcoin", "https://www.sec.gov/Archives/edgar/data/1763415/000119312526340183/bitb-20260630.htm"],
 "hodl": ["VanEck Bitcoin ETF (HODL) Form 10-Q, June 30, 2026: 16,241.00 bitcoin", "https://www.sec.gov/Archives/edgar/data/1838028/000093041326002505/c117299_10q-ixbrl.htm"],
 "mstr": ["Strategy Inc Form 8-K filed Oct 26, 2026: holds approximately 848,517 bitcoin as of Oct 25, 2026", "https://www.sec.gov/Archives/edgar/data/1050446/000119312526431146/mstr-20261026.htm"],
 "xxi": ["Twenty One Capital, Inc. Form 10-Q, June 30, 2026: held 43,514 Bitcoin", "https://www.sec.gov/Archives/edgar/data/2070457/000121390026087471/ea0299640-10q_twentyone.htm"],
 "mara": ["MARA Holdings Form 10-Q, June 30, 2026, Note 5: total bitcoin holdings 35,577 (26,307 held + 9,270 receivable)", "https://www.sec.gov/Archives/edgar/data/1507605/000150760526000022/mara-20260630.htm"],
 "tsla": ["Tesla, Inc. Form 10-Q, September 30, 2026: 11,509 units of Bitcoin", "https://www.sec.gov/Archives/edgar/data/1318605/000162828026066775/tsla-20260930.htm"],
 "riot": ["Riot Platforms Form 10-Q, June 30, 2026: held 11,380 bitcoin", "https://www.sec.gov/Archives/edgar/data/1167419/000110465926093448/riot-20260630x10q.htm"],
 "chain": ["CryptoSlate, June 20, 2020, reporting Chainalysis: 3.7 million of 18.6 million BTC mined had been lost. Chainalysis's own page was not located, so this is a secondary source", "https://cryptoslate.com/this-chainalysis-report-reveals-a-stunningly-optimistic-trend-for-the-crypto-market/"],
 "chain2": ["Chainalysis: \"Why Bitcoin is Surging and How This Rally Is Different from 2017\" (defines lost coins as unmoved for five years or longer)", "https://www.chainalysis.com/blog/bitcoin-price-surge-explained-2020/"],
 "patoshi": ["Sergio Lerner, Bitslog, Apr 16, 2019: analysis that one early miner (\"Patoshi\") mined close to 1.1 million coins", "https://bitslog.com/2019/04/16/the-return-of-the-deniers-and-the-revenge-of-patoshi/"],
}

# ---- holders
ETF = [("iShares Bitcoin Trust (IBIT)", 811160.8205, "Oct 26, 2026", "ibit"), ("Fidelity Wise Origin (FBTC)", 174383, "Jun 30, 2026", "fbtc"),
       ("Grayscale Bitcoin Trust (GBTC)", 138505.7568, "Jun 30, 2026", "gbtc"), ("Bitwise Bitcoin ETF (BITB)", 36207.6919, "Jun 30, 2026", "bitb"),
       ("ARK 21Shares Bitcoin ETF (ARKB)", 32178.2280, "Jun 30, 2026", "arkb"), ("VanEck Bitcoin ETF (HODL)", 16241.00, "Jun 30, 2026", "hodl")]
CO = [("Strategy Inc (MSTR)", 848517, "Oct 25, 2026", "mstr"), ("Twenty One Capital (XXI)", 43514, "Jun 30, 2026", "xxi"), ("MARA Holdings (MARA)", 35577, "Jun 30, 2026", "mara"),
      ("Tesla (TSLA)", 11509, "Sep 30, 2026", "tsla"), ("Riot Platforms (RIOT)", 11380, "Jun 30, 2026", "riot")]
etf_t = sum(x[1] for x in ETF); strat = CO[0][1]; co_other = sum(x[1] for x in CO[1:])
LOST = 3_700_000
resid = circ - etf_t - strat - co_other - LOST
fm = lambda v, n=0: f"{v:,.{n}f}"

sec = []
sec.append({"id": "ticker", "title": "Bitcoin, live", "blocks": [{"type": "ticker", "period_seconds": 600, "period_label": "a block",
  "label": "estimate: 3.125 BTC per block at the 10-minute target",
  "counters": [{"id": "iss", "label": "New bitcoin issued by the protocol (estimate)", "annual": subsidy, "unit": "btc", "hero": True}],
  "note": f"Each block creates {subsidy} BTC (the block subsidy since the April 2024 halving) and blocks arrive about every 10 minutes by design, so {subsidy} ÷ 600 s = {per_s:.4f} BTC a second. This is an estimate: blocks actually arrive at random. Since block 840,000 the average gap has been {avg:.0f} s (derived from the timestamps of blocks 840,000 and {tip_h:,}), so real issuance runs a little faster. Transaction fees are extra and not counted here. The counter shows the target rate multiplied by time, not blocks found. [[core]] [[mempool]]",
  "facts": [["Circulating supply", f"{fm(circ)} BTC"], ["Hard cap", "21,000,000 BTC"], ["Block height", f"{tip_h:,}"], ["Next halving (est.)", utc(estavg).strftime("%b %Y")]]}]})

sec.append({"id": "supply", "title": "Supply", "lede": f"Bitcoin's rules cap supply at 21 million coins. As of {as_of}, {fm(circ)} had been created, {circ / 21e6 * 100:.1f}% of the cap. [[bci]]",
  "blocks": [{"type": "stats", "items": [["Created so far", f"{fm(circ)} BTC", f"Public API, block {tip_h:,} [[bci]]"], ["Not yet created", f"{fm(not_mined)} BTC", "Cap 20,999,999.9769 less created (derived) [[core]] [[bci]]"],
       ["Share created", f"{circ / CAP * 100:.2f}%", "Derived"], ["Annual new supply at current rate", f"{subsidy * 144 * 365 / circ * 100:.2f}%", f"{subsidy * 144 * 365:,.0f} BTC a year at 144 blocks a day ÷ supply (derived estimate)"]]},
    {"type": "math", "title": "Checking supply from the rules", "lines": [
       "Subsidy: 50 BTC per block, halving every 210,000 blocks. [[core]]",
       f"Blocks 0 to 839,999 (four full eras): 210,000 × (50 + 25 + 12.5 + 6.25) = {fm(sum(e[4] for e in eras[:4]))} BTC",
       f"Blocks 840,000 to {tip_h:,} at {subsidy} BTC: {tip_h - 840000 + 1:,} × {subsidy} = {fm((tip_h - 839999) * subsidy, 3)} BTC",
       f"= **{fm(mined_math, 3)} BTC** if every subsidy was fully claimed (derived).",
       f"The API reports {fm(circ, 1)} BTC created. The gap of about {mined_math - circ:,.0f} BTC is because some miners claimed less than the full subsidy; the API counts coins actually created. [[bci]]",
       "Adding all 33 eras gives 20,999,999.9769 BTC, the exact cap (the subsidy is rounded down to whole satoshis, so it is just under 21 million)."]}]})

wf = [{"label": "US spot bitcoin ETFs (six funds, table below)", "value": etf_t, "src": ["ibit", "fbtc", "gbtc", "bitb", "arkb", "hodl"]},
      {"label": "Strategy Inc", "value": strat, "src": ["mstr"]},
      {"label": "Four other public companies (XXI, MARA, TSLA, RIOT)", "value": co_other, "src": ["xxi", "mara", "tsla", "riot"]},
      {"label": "Dormant five years or more: estimated lost (Chainalysis, 2020)", "value": LOST, "est": True, "est_label": "estimate", "src": ["chain", "chain2"]},
      {"label": "Everything else created: owners not public (derived)", "value": resid, "color": "#3a4252", "src": ["bci"]},
      {"label": "Not yet created", "value": not_mined, "color": "#e8edf5", "src": ["core", "bci"]}]
sec.append({"id": "holders", "title": "Who holds it", "lede": "Bitcoin is pseudonymous, so only some holders can be named. Here are the ones with published figures, one square per 100,000 BTC.",
  "blocks": [{"type": "waffle", "title": "All 21 million bitcoin by holder", "unit": "BTC", "dec": 0, "cell": 100000, "cell_label": "100,000 BTC", "cols": 21, "items": wf, "total_label": "Hard cap",
    "note": f"Holdings are the latest figures each holder has published, so the dates differ (shown in the tables below). The estimate is Chainalysis's June 2020 count of 3.7 million BTC that had not moved for five years or longer, treated as lost; that was a 2020 figure, and some of those coins may simply be held, so the hatched block is a rough estimate. Wallets of exchanges, governments, funds and individuals are not published and sit in \"everything else\", which is the supply created less the named holders and the lost estimate. Only holdings in SEC filings or issuers' own pages are named; no on-chain \"whale\" or government-wallet estimates are used. [[chain]] [[bci]]"}]})

sec.append({"id": "halving", "title": "Issuance and the halving", "lede": f"The reward per block halves every 210,000 blocks, about every four years. It is {subsidy} BTC now. [[core]]",
  "blocks": [
   {"type": "stats", "items": [["Reward per block now", f"{subsidy} BTC", "Since block 840,000 [[core]]"], ["Reward per day at 144 blocks", f"{subsidy * 144:,.0f} BTC", "Target pace, estimate [[core]]"],
      ["Blocks to next halving", f"{left + 1:,}", f"Block {next_h:,} is the next halving (derived from height {tip_h:,}) [[mempool]]"],
      ["Next halving (estimate)", utc(estavg).strftime("%b %Y"), f"{d(estavg)} at the recent {avg:.0f}-second average; {d(est600)} at exactly 10 minutes. Block times vary, so this is an estimate"]]},
   {"type": "table", "title": "Halving schedule", "cols": ["Era", "Blocks", "Reward per block", "BTC issued in era", "Cumulative supply", "Started"], "align": "lllrrl",
    "rows": [[str(i + 1), f"{a:,} – {b:,}", f"{r:g} BTC", fm(t, 1 if t % 1 else 0), fm(sum(e[4] for e in eras[:i + 1]), 1 if sum(e[4] for e in eras[:i + 1]) % 1 else 0), (d(TS[a]) + " (actual)" if a in TS else d(est600 + (a - next_h) * 600 if a > next_h else estavg) + " (estimate)" if a != next_h else d(estavg) + " (estimate)")] for i, a, b, r, t in [(e[0], e[1], e[2], e[3], e[4]) for e in eras[:10]]],
    "src": ["core", "mempool"], "note": "Actual start dates are the timestamps of the first block of each era (UTC, mempool.space). Future dates assume 10-minute blocks from the chain tip and are estimates. After era 33 (around the year 2140) the reward rounds down to zero. Showing the first ten of 33 eras. [[core]] [[mempool]]"}]})

fund_rows = [[n, fm(v, 0), dte, f"[[{k}]]"] for n, v, dte, k in ETF] + [["Total, six funds", fm(etf_t, 0), "mixed dates", "Derived sum"]]
sec.append({"id": "funds", "title": "US spot bitcoin ETFs", "lede": "Each fund reports the bitcoin its custodian holds for it. IBIT's figure is from the issuer's page; the others are from their latest quarterly reports to the SEC (Form 10-Q, June 30, 2026). [[ibit]]",
  "blocks": [{"type": "table", "cols": ["Fund", "Bitcoin held (BTC)", "As of", "Source"], "align": "lrll", "rows": fund_rows,
    "note": f"IBIT held 734,261 BTC at June 30, 2026 per its 10-Q, against {fm(ETF[0][1], 0)} BTC on its page for Oct 26, 2026. Other US spot funds (for example the Grayscale Bitcoin Mini Trust, Invesco Galaxy, CoinShares, Franklin and WisdomTree funds) are not in this total. [[ibit]] [[ibit_q]]"}]})

co_rows = [[n, fm(v, 0), dte, f"[[{k}]]"] for n, v, dte, k in CO] + [["Total, five companies", fm(strat + co_other, 0), "mixed dates", "Derived sum"]]
sec.append({"id": "companies", "title": "Public companies", "lede": "US-listed companies that state their bitcoin in SEC filings. Figures are the latest filed. [[mstr]]",
  "blocks": [{"type": "table", "cols": ["Company", "Bitcoin held (BTC)", "As of", "Source"], "align": "lrll", "rows": co_rows,
    "note": "Strategy's figure is from its Form 8-K for Oct 25, 2026 (\"approximately\"). MARA's 35,577 includes 9,270 BTC it reports as receivable (lent to counterparties). Tesla's 10-Q says most of its digital assets are 11,509 units of bitcoin. Other public holders, companies outside the SEC system and governments are not listed, because no free official figure was checked for them. [[mara]] [[tsla]]"}]})

tl = [{"date": d(TS[0]), "text": "Genesis block (block 0).", "src": ["mempool"]},
      {"date": d(TS[210000]), "text": "First halving, at block 210,000: the reward falls from 50 to 25 BTC.", "src": ["mempool", "core"]},
      {"date": d(TS[420000]), "text": "Second halving, at block 420,000: 25 to 12.5 BTC.", "src": ["mempool", "core"]},
      {"date": d(TS[630000]), "text": "Third halving, at block 630,000: 12.5 to 6.25 BTC.", "src": ["mempool", "core"]},
      {"date": "Jan 5, 2024", "text": "iShares Bitcoin Trust (IBIT) is incepted, per the issuer's fund page. US spot bitcoin ETFs begin.", "src": ["ibit"]},
      {"date": d(TS[840000]), "text": "Fourth halving, at block 840,000: 6.25 to 3.125 BTC.", "src": ["mempool", "core"]},
      {"date": as_of, "text": f"Block {tip_h:,}: {fm(circ)} BTC created, {circ / CAP * 100:.1f}% of the cap.", "src": ["bci", "mempool"]},
      {"date": utc(estavg).strftime("%Y") + " (estimate)", "text": f"Fifth halving, at block {next_h:,}: 3.125 to 1.5625 BTC. Timing depends on block times.", "src": ["core"]}]
tl_sorted = tl
sec.append({"id": "timeline", "title": "Timeline", "lede": "Protocol milestones, with dates taken from block timestamps (UTC).", "blocks": [{"type": "timeline", "items": tl_sorted}]})

e = {"type": "commodity", "template": "bitcoin", "slug": "bitcoin", "order": 30, "live": True, "name": "Bitcoin", "symbol": "BTC",
 "title": "Where all the bitcoin is: supply, halvings, and who holds it",
 "description": f"Bitcoin's supply is capped at 21 million; about {circ / 1e6:.1f} million exist. See the halving schedule, the bitcoin held by US spot ETFs and public companies from SEC filings, and an estimate of lost coins.",
 "tagline": f"{circ / 1e6:.2f} million of 21 million created. About {etf_t / 1e6 + (strat + co_other) / 1e6:.1f} million are held by ETFs and public companies that publish it.",
 "card_stat": {"label": "Issued per second (est.)", "value": f"~{per_s:.4f} BTC", "note": f"{subsidy} BTC a block, 10-minute target"},
 "as_of": f"chain data {as_of}; holders from SEC filings and issuer pages (dates shown)",
 "sources": src, "sections": sec}
json.dump(e, open(f"{HERE}/data/bitcoin.json", "w"), indent=1, ensure_ascii=False)
print("btc ok", circ, mined_math, tip_h, d(estavg), d(est600), resid, avg)
