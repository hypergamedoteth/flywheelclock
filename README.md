# Flywheel Clock (draft)

How big companies and commodities really work: live money clocks plus sourced data and stories.
Static site, no dependencies beyond Python 3. **Local draft only. Nothing is deployed and the domain is not bought.**

## Build and preview
    python3 build.py              # draft: DRAFT banner, noindex, "verify before launch" badges shown
    python3 build.py --launch     # launch: no banner, indexable, items with "verify": true are left out
    python3 -m http.server 8765   # then open http://127.0.0.1:8765/
    node ../tools/shoot.js        # full-page screenshots -> ../screenshots/ (+ console error check)

## Layout
- `data/<slug>.json`: one file per company or commodity (the only thing you edit to add pages)
- `templates/company.html`, `templates/commodity.html`: section order (`{{section:<id>}}`); `base.html`, `home.html`
- `assets/style.css`, `assets/clock.js` (tickers: annual ÷ period seconds × elapsed seconds)
- `tools/seed_*.py`: scripts that write the data files (costco, companies (apple/amazon/american-express), gold, oil, bitcoin). `tools/add_visuals.py` then adds the paired bars, live Sankey, flywheel loop and gold waffle to the company/gold files. Run seeds first, then `python3 tools/add_visuals.py && python3 build.py`.
- Optional entry keys: `"template"` (use `templates/<name>.html` instead of the type default) and `"order"` (sort order on hub and homepage). Ticker units: usd, gold, btc, bbl.
- Generated output (committed so it can be previewed): `index.html`, `companies/`, `commodities/`, `sitemap.xml`, `robots.txt`, `404.html`

## Add a company (one file)
1. Copy `data/costco.json` to `data/<slug>.json` (slug: lowercase letters, digits and dashes).
2. Set `"type": "company"`, `"slug"`, `"live": true`, `"name"`, `"ticker_symbol"`, `"title"`, `"description"`, `"tagline"`, `"as_of"`, and `"card_stat": {"label","value","note"}` for the homepage card.
3. `"sources"`: `{"id": ["Name of source", "https://url or empty"]}`. Cite in any text with `[[id]]`; `**bold**` works.
4. `"sections"`: a list of `{"id","title","lede","blocks":[...]}`. Company ids used by the template: `ticker, flow, employees, geography, decisions, timeline`. A missing section shows "Data pending" in draft builds and is hidden in launch builds.
5. Block types: `ticker` (counters with `annual`, `unit` usd|gold, one `hero`), `sankey` (set `live`, `period_seconds`, `period_text` for per-node per-second counters; nodes `{id,label,col,kind}` with kind in/key/mid/cost/profit; links `[from,to,value_in_millions]`), `pairs` (two stacked bars side by side: revenue vs operating profit by segment), `loop` (animated flywheel of steps with filed numbers on the arrows), `waffle` (holder grid, one square per fixed unit, hatched = estimate), `stats`, `bars`, `table` (rows can be `{"cells":[...],"verify":true}`), `statemap` (`items` with `abbr,name,warehouses,value`), `cards`, `timeline`, `stack`, `math`, `note`, `list`, `pending`. Any item with `"verify": true` gets a badge in drafts and is dropped from launch builds.
6. Run `python3 build.py`. The page, homepage card, hub page, nav and sitemap update automatically. Set `"live": false` to keep a file out of the site (there are no "coming soon" placeholders).

Commodities work the same way with `"type": "commodity"`, `"symbol"`, and the section ids in `templates/commodity.html`.

## Data rules
Every number comes from a cited source or is labelled "derived" with its math shown. Oil uses OPEC ASB, EIA and NRCan. Bitcoin uses public chain APIs, SEC filings and issuer pages; estimates (live issuance rate, lost coins, future halving dates) are labelled. Gold uses free data only (USGS, IMF IRFCL, issuers, Tether, official vault disclosures). **No World Gold Council figures.**
