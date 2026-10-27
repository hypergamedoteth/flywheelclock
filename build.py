#!/usr/bin/env python3
"""Flywheel Clock static site builder.

  python3 build.py            # draft build (default): draft banner, noindex, unverified items shown with a badge
  python3 build.py --launch   # launch build: no banner, indexable, items marked "verify" are left out

Adding a company or commodity = drop one JSON file in data/ (see README.md). Pages, hubs,
homepage cards, nav and sitemap are all generated from data/*.json. Entries with "live": false are skipped.
"""
import glob, hashlib, html, json, math, os, re, shutil, sys
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE_URL = "https://flywheelclock.com"
LAUNCH = "--launch" in sys.argv
TYPES = {"company": ("companies", "Companies"), "commodity": ("commodities", "Commodities")}

def read(p): return open(os.path.join(ROOT, p), encoding="utf-8").read()
def esc(s): return html.escape(str(s), quote=True)
def vhash(p): return hashlib.sha1(open(os.path.join(ROOT, p), "rb").read()).hexdigest()[:10]

def fill(tpl, **kw):
    return re.sub(r"\{\{(\w+)\}\}", lambda m: str(kw.get(m.group(1), "")), tpl)

# ---------------------------------------------------------------- formatting
def money(v, d=1):
    a = abs(v); s = "−$" if v < 0 else "$"
    for div, suf in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
        if a >= div: return f"{s}{a / div:,.{d}f}{suf}"
    return f"{s}{a:,.0f}"

def qty(v, unit):
    if unit == "usd": return money(v)
    if unit == "t": return f"{v:,.0f} t" if v >= 100 or v == int(v) else f"{v:,.1f} t"
    if unit == "bbl": return f"{v:,.0f} bbl" if v < 1e9 else f"{v/1e9:,.1f}B bbl"
    if unit == "btc": return f"{v:,.0f} BTC"
    if unit == "bpd": return f"{v / 1e6:,.2f}M bbl/d"
    return f"{v:,.0f}"

class Page:
    """Per-page render context: source numbering and verify handling."""
    def __init__(self, entry):
        self.e = entry
        self.src = entry.get("sources", {})
        self.order = list(self.src)
        self.cited = set()
        self.live = []      # live counters registered by blocks (sankey nodes)

    def cite(self, sid):
        if sid not in self.src: return f'<sup class="cite miss">[{esc(sid)}?]</sup>'
        self.cited.add(sid); n = self.order.index(sid) + 1
        return f'<sup class="cite"><a href="#src-{esc(sid)}" title="{esc(self.src[sid][0])}">{n}</a></sup>'

    def rich(self, text):
        s = esc(text)
        s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
        return re.sub(r"\[\[([\w-]+)\]\]", lambda m: self.cite(m.group(1)), s)

    def cites(self, ids): return "".join(self.cite(i) for i in ids or [])

    def keep(self, item):
        return not (LAUNCH and isinstance(item, dict) and item.get("verify"))

    def badge(self, item):
        return ' <span class="badge warn">verify before launch</span>' if isinstance(item, dict) and item.get("verify") else ""

# ---------------------------------------------------------------- blocks
def b_ticker(P, b):
    hero = next((c for c in b["counters"] if c.get("hero")), b["counters"][0])
    rest = [c for c in b["counters"] if c is not hero]
    per = lambda c: c["annual"] / b["period_seconds"]
    def rate(c):
        r = per(c)
        if c["unit"] == "usd": return f"${r:,.0f}"
        if c["unit"] == "bbl": return f"{r:,.0f} bbl"
        if c["unit"] == "btc": return f"{r:,.4f} BTC"
        return f"{r/1000:,.3f} kg"
    tiles = "".join(
        f'<div class="ctile"><div class="l">{esc(c["label"])}</div>'
        f'<div class="num" data-ctr="{esc(c["id"])}" data-mode="year">{rate(c)}/s</div>'
        f'<div class="s"><span class="num">{rate(c)}</span> a second · <span class="num" data-ctr="{esc(c["id"])}" data-mode="open">0</span> since you opened this page</div></div>'
        for c in rest)
    facts = "".join(f'<div><span class="l">{esc(k)}</span><span class="num">{esc(v)}</span></div>' for k, v in b.get("facts", []))
    unit_word = "since Jan 1" 
    return (f'<div class="hero"><div class="k">{esc(hero["label"])} {unit_word} <span class="tag">{esc(b["label"])}</span></div>'
            f'<div class="big num" data-ctr="{esc(hero["id"])}" data-mode="year">{rate(hero)} a second</div>'
            f'<div class="sub"><span><span class="num" data-ctr="{esc(hero["id"])}" data-mode="open">0</span> since you opened this page</span>'
            f'<span><span class="num">{rate(hero)}</span> a second</span>'
            f'<span><span class="num" data-ctr="{esc(hero["id"])}" data-mode="day">—</span> a day</span></div>'
            + (f'<div class="facts">{facts}</div>' if facts else "") + '</div>'
            + (f'<div class="ctiles">{tiles}</div>' if tiles else "")
            + f'<p class="fine">{P.rich(b.get("note", ""))}</p>')

KIND_COL = {"in": "#3fb8af", "key": "#f2b84b", "mid": "#8aa4c8", "cost": "#e0656f", "profit": "#4cc38a"}

def rate_txt(v):
    """US$/second text for a US$ annual amount."""
    a = abs(v)
    if a >= 1e6: return f"${v/1e6:,.1f}M/s"
    if a >= 1e3: return f"${v/1e3:,.1f}K/s"
    return f"${v:,.0f}/s"

def b_sankey(P, b):
    live = bool(b.get("live")); secs = b.get("period_seconds")
    nodes = {n["id"]: dict(n, ins=0, outs=0) for n in b["nodes"]}
    for s, t, v in b["links"]: nodes[s]["outs"] += v; nodes[t]["ins"] += v
    for n in nodes.values(): n["v"] = max(n["ins"], n["outs"])
    ncol = max(n["col"] for n in nodes.values()) + 1
    cols = [[n for n in b["nodes"] if n["col"] == c] for c in range(ncol)]
    cols = [[nodes[n["id"]] for n in c] for c in cols]
    W, LM, RM, NW, GAP, HI, SLOT = (1320 if live else 1100), 300, (250 if live else 300), 12, 16, 360, (58 if live else 34)
    maxtot = max(sum(n["v"] for n in c) for c in cols)
    k = (HI - GAP * (max(len(c) for c in cols) - 1)) / maxtot
    xs = [LM + i * (W - LM - RM - NW) / max(ncol - 1, 1) for i in range(ncol)]
    for n in nodes.values(): n["h"] = max(n["v"] * k, 1.5); n["so"] = 0; n["to"] = 0
    # col 0 stacked from the top; later columns placed near their sources, then de-overlapped
    y = 10
    for n in cols[0]: n["y"] = y; y += max(n["h"], SLOT) + GAP
    links = [dict(s=nodes[s], t=nodes[t], v=v) for s, t, v in b["links"]]
    for c in range(1, ncol):
        for n in cols[c]:
            ins = [l for l in links if l["t"] is n]
            if ins:
                # where the link would start on the source side
                ys = []
                for l in ins:
                    off = 0
                    for l2 in links:
                        if l2["s"] is l["s"]:
                            if l2 is l: break
                            off += l2["v"] * k
                    ys.append(l["s"]["y"] + off)
                n["y"] = min(ys)
            else:
                n["y"] = None
        prev = None
        for n in cols[c]:
            if n["y"] is None: n["y"] = (prev["y"] + max(prev["h"], SLOT) + GAP) if prev else 10
            if prev and n["y"] < prev["y"] + max(prev["h"], SLOT) + GAP: n["y"] = prev["y"] + max(prev["h"], SLOT) + GAP
            prev = n
    H = max(n["y"] + max(n["h"], SLOT) for n in nodes.values()) + 14
    out = []; flows = []
    for l in links:
        s, t = l["s"], l["t"]; h = l["v"] * k
        x1, x0 = xs[s["col"]] + NW, xs[t["col"]]
        sy, ty = s["y"] + s["so"], t["y"] + t["to"]; s["so"] += h; t["to"] += h
        xm = (x1 + x0) / 2
        col = KIND_COL[t["kind"] if t["kind"] != "mid" else s["kind"]]
        out.append(f'<path d="M{x1:.1f},{sy:.1f}C{xm:.1f},{sy:.1f} {xm:.1f},{ty:.1f} {x0:.1f},{ty:.1f}L{x0:.1f},{ty + h:.1f}C{xm:.1f},{ty + h:.1f} {xm:.1f},{sy + h:.1f} {x1:.1f},{sy + h:.1f}Z" fill="{col}" opacity=".32"><title>{esc(s["label"])} → {esc(t["label"])}: {money(l["v"] * 1e6)}</title></path>')
        if live:
            flows.append(f'<path class="fl" d="M{x1:.1f},{sy + h / 2:.1f}C{xm:.1f},{sy + h / 2:.1f} {xm:.1f},{ty + h / 2:.1f} {x0:.1f},{ty + h / 2:.1f}" stroke-width="{max(1.4, min(h * .35, 7)):.1f}"/>')
    out += flows
    der = set(b.get("derived", []))
    bid = b.get("id", "sk")
    for n in nodes.values():
        x = xs[n["col"]]; cy = n["y"] + n["h"] / 2
        out.append(f'<rect x="{x:.1f}" y="{n["y"]:.1f}" width="{NW}" height="{n["h"]:.1f}" rx="2" fill="{KIND_COL[n["kind"]]}"/>')
        if n["col"] == 0: tx, anc = x - 8, "end"
        elif n["col"] == ncol - 1: tx, anc = x + NW + 8, "start"
        else: tx, anc = x + NW + 6, "start"
        val = money(n["v"] * 1e6) + (" †" if n["id"] in der else "")
        t0 = max(cy - (14 if live else 1), 16)
        out.append(f'<text x="{tx:.1f}" y="{t0:.1f}" text-anchor="{anc}" class="nl">{esc(n["label"])}</text>'
                   f'<text x="{tx:.1f}" y="{t0 + 14:.1f}" text-anchor="{anc}" class="nv">{val}</text>')
        if live:
            cid = f"{bid}-{n['id']}"; r = n["v"] * 1e6 / secs
            P.live.append(dict(id=cid, unit="usd", rate=r))
            out.append(f'<text x="{tx:.1f}" y="{t0 + 28:.1f}" text-anchor="{anc}" class="nc"><tspan data-ctr="{cid}" data-mode="year" data-fmt="c">{money(r)}</tspan><tspan class="nr"> · {rate_txt(r)}</tspan></text>')
    svg = f'<svg viewBox="0 0 {W} {H:.0f}" role="img" aria-label="{esc(b.get("title", "Flow"))}">{"".join(out)}</svg>'
    extra = ""
    if live:
        rows = "".join(f'<tr><td>{esc(n["label"])}{" †" if n["id"] in der else ""}</td><td class="r num">{money(n["v"] * 1e6, 2)}</td><td class="r num">{rate_txt(n["v"] * 1e6 / secs)}</td></tr>' for n in nodes.values())
        lrows = "".join(f'<tr><td>{esc(l["s"]["label"])} → {esc(l["t"]["label"])}</td><td class="r num">{money(l["v"] * 1e6, 2)}</td><td class="r num">{rate_txt(l["v"] * 1e6 / secs)}</td></tr>' for l in links)
        extra = (f'<p class="fine"><b>Per-second basis:</b> {esc(b.get("period_text", ""))} The counters are projections from that average, not live sales. † = derived (calculated from filed figures, math in the note).</p>'
                 f'<details><summary>Every node and flow as text ({len(nodes)} nodes, {len(links)} flows)</summary><div class="tw"><table class="v"><thead><tr><th>Node</th><th class="r">Fiscal year</th><th class="r">Per second</th></tr></thead><tbody>{rows}</tbody></table></div>'
                 f'<div class="tw"><table class="v"><thead><tr><th>Flow</th><th class="r">Fiscal year</th><th class="r">Per second</th></tr></thead><tbody>{lrows}</tbody></table></div></details>')
    return (f'<figure class="sk{" live" if live else ""}"><figcaption>{esc(b.get("title", ""))}{" <span class=\"badge ok\">live flow</span>" if live else ""}</figcaption><p class="skhint">Scroll sideways to follow the money →</p><div class="skw">{svg}</div>'
            f'<p class="fine">{P.rich(b.get("note", ""))}</p>{extra}</figure>')

def b_stats(P, b):
    items = "".join(f'<div class="stat"><div class="l">{esc(l)}</div><div class="v num">{esc(v)}</div><div class="s">{P.rich(s)}</div></div>'
                    for l, v, s in b["items"])
    return f'<div class="stats">{items}</div>'

def b_bars(P, b):
    mx = max(v for _, v in b["items"])
    rows = "".join(f'<div class="bar"><span class="bl">{esc(l)}</span><span class="bt"><i style="width:{v / mx * 100:.2f}%"></i></span><span class="bv num">{qty(v, b.get("unit"))}</span></div>'
                   for l, v in b["items"])
    note = f'<p class="fine">{P.rich(b["note"])}</p>' if b.get("note") else ""
    return f'<div class="card"><h3>{esc(b.get("title", ""))}{P.cites(b.get("src"))}</h3><div class="bars">{rows}</div>{note}</div>'

def b_table(P, b):
    al = b.get("align", "l" * len(b["cols"]))
    th = "".join(f'<th class="{"r" if al[i] == "r" else ""}">{esc(c)}</th>' for i, c in enumerate(b["cols"]))
    trs = []
    for r in b["rows"]:
        if not P.keep(r): continue
        cells = r["cells"] if isinstance(r, dict) else r
        tds = "".join(f'<td class="{"r num" if al[i] == "r" else ""}">{P.rich(c)}{P.badge(r) if i == len(cells) - 1 else ""}</td>' for i, c in enumerate(cells))
        trs.append(f"<tr>{tds}</tr>")
    title = f'<h3>{esc(b["title"])}{P.cites(b.get("src"))}</h3>' if b.get("title") else ""
    note = f'<p class="fine">{P.rich(b["note"])}</p>' if b.get("note") else ""
    return f'<div class="card{" compact" if b.get("compact") else ""}">{title}<div class="tw"><table class="v"><thead><tr>{th}</tr></thead><tbody>{"".join(trs)}</tbody></table></div>{note}</div>'

TILES = {"AK": (0, 0), "ME": (11, 0), "VT": (10, 1), "NH": (11, 1), "WA": (1, 2), "ID": (2, 2), "MT": (3, 2), "ND": (4, 2), "MN": (5, 2), "IL": (6, 2), "WI": (7, 2), "MI": (8, 2), "NY": (9, 2), "RI": (10, 2), "MA": (11, 2),
         "OR": (1, 3), "NV": (2, 3), "WY": (3, 3), "SD": (4, 3), "IA": (5, 3), "IN": (6, 3), "OH": (7, 3), "PA": (8, 3), "NJ": (9, 3), "CT": (10, 3),
         "CA": (1, 4), "UT": (2, 4), "CO": (3, 4), "NE": (4, 4), "MO": (5, 4), "KY": (6, 4), "WV": (7, 4), "VA": (8, 4), "MD": (9, 4), "DE": (10, 4),
         "AZ": (2, 5), "NM": (3, 5), "KS": (4, 5), "AR": (5, 5), "TN": (6, 5), "NC": (7, 5), "SC": (8, 5), "DC": (9, 5),
         "OK": (4, 6), "LA": (5, 6), "MS": (6, 6), "AL": (7, 6), "GA": (8, 6), "HI": (0, 7), "TX": (4, 7), "FL": (9, 7), "PR": (11, 7)}

def b_statemap(P, b):
    by = {s["abbr"]: s for s in b["items"]}
    mx = max(math.log10(s["value"]) for s in b["items"]); mn = min(math.log10(s["value"]) for s in b["items"])
    S, G = 54, 4; out = []
    for ab, (cx, cy) in TILES.items():
        x, y = cx * (S + G), cy * (S + G); s = by.get(ab)
        if s:
            t = (math.log10(s["value"]) - mn) / (mx - mn or 1)
            fill = f"rgba(242,184,75,{0.14 + 0.78 * t:.2f})"; lab = money(s["value"])
            tip = f'{s["name"]}: {money(s["value"])} est. ({s["warehouses"]} warehouses)' + (" — anchored to the 10-K" if s.get("anchored") else "")
            tc = "#0a0c10" if t > .55 else "#e9edf3"
        else:
            fill, lab, tip, tc = "#141922", "none", f"{ab}: no warehouses listed", "#5d6878"
        out.append(f'<g><title>{esc(tip)}</title><rect x="{x}" y="{y}" width="{S}" height="{S}" rx="6" fill="{fill}" stroke="#232b38"/>'
                   f'<text x="{x + S / 2}" y="{y + 23}" text-anchor="middle" class="ta" fill="{tc}">{ab}</text>'
                   f'<text x="{x + S / 2}" y="{y + 40}" text-anchor="middle" class="tv" fill="{tc}">{lab}</text></g>')
    W, H = 12 * (S + G), 8 * (S + G)
    svg = f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{esc(b["title"])}">{"".join(out)}</svg>'
    rows = sorted(b["items"], key=lambda s: -s["value"])
    trs = "".join(f'<tr><td>{esc(s["name"])}{" <span class=\"badge ok\">from 10-K</span>" if s.get("anchored") else ""}</td><td class="r num">{s["warehouses"]}</td><td class="r num">{money(s["value"])}</td></tr>' for s in rows)
    method = "".join(f"<li>{P.rich(m)}</li>" for m in b.get("method", []))
    return (f'<div class="card est"><h3>{esc(b["title"])} <span class="badge warn">ESTIMATE</span></h3>'
            f'<div class="banner">{esc(b.get("banner", ""))}</div><div class="mapw">{svg}</div>'
            f'<details><summary>Method and full table ({len(rows)} states and territories)</summary><ol class="method">{method}</ol>'
            f'<div class="tw"><table class="v"><thead><tr><th>State</th><th class="r">Warehouses</th><th class="r">Est. revenue</th></tr></thead><tbody>{trs}</tbody></table></div></details>'
            f'<p class="fine">{P.rich(b.get("note", ""))}</p></div>')

def b_cards(P, b):
    cs = "".join(f'<article class="story"><div class="kick">{esc(c["kicker"])}</div><div class="big num">{esc(c["big"])}</div>'
                 f'<h3>{esc(c["title"])}</h3><p>{P.rich(c["text"])}{P.cites(c.get("src"))}</p></article>' for c in b["items"] if P.keep(c))
    return f'<div class="stories">{cs}</div>'

def b_timeline(P, b):
    lis = "".join(f'<li><div class="td">{esc(i["date"])}</div><div class="tx">{P.rich(i["text"])}{P.cites(i.get("src"))}{P.badge(i)}'
                  + (f'<div class="tw2">{esc(i["where"])}</div>' if i.get("where") else "") + '</div></li>'
                  for i in b["items"] if P.keep(i))
    note = f'<p class="fine">{P.rich(b["note"])}</p>' if b.get("note") and not LAUNCH else ""
    return f'<ol class="timeline">{lis}</ol>{note}'

STACK_COL = {"official": "#f2b84b", "official2": "#c99a3e", "etf": "#3fb8af", "co": "#8aa4c8", "private": "#3a4252"}

def b_stack(P, b):
    tot = b["total"]
    segs = "".join(f'<i style="width:{it["value"] / tot * 100:.3f}%;background:{STACK_COL[it["kind"]]}" title="{esc(it["label"])}"></i>' for it in b["items"])
    rows = "".join(f'<tr><td><span class="sw" style="background:{STACK_COL[it["kind"]]}"></span>{esc(it["label"])}{P.cites(it.get("src"))}</td>'
                   f'<td class="r num">{it["value"]:,.1f} t</td><td class="r num">{it["value"] / tot * 100:.1f}%</td></tr>' for it in b["items"])
    return (f'<div class="card"><p class="headline">{esc(b.get("headline", ""))}</p><div class="stack">{segs}</div>'
            f'<div class="tw"><table class="v"><thead><tr><th>Owner</th><th class="r">Tonnes</th><th class="r">Share</th></tr></thead><tbody>{rows}'
            f'<tr class="tot"><td>Approx. gold ever mined</td><td class="r num">{tot:,.0f} t</td><td class="r num">100%</td></tr></tbody></table></div></div>')

def b_math(P, b):
    lis = "".join(f"<li>{P.rich(l)}</li>" for l in b["lines"])
    note = f'<p class="fine">{P.rich(b["note"])}</p>' if b.get("note") else ""
    return f'<div class="card math"><h3>{esc(b.get("title", ""))}</h3><ul>{lis}</ul>{note}</div>'

def b_note(P, b): return f'<p class="note">{P.rich(b["text"])}</p>'

def b_list(P, b):
    lis = "".join(f"<li>{P.rich(i['text'])}{P.badge(i)}</li>" for i in b["items"] if P.keep(i))
    return f'<div class="card"><h3>{esc(b.get("title", ""))}</h3><ul class="plain">{lis}</ul></div>'

def b_pending(P, b):
    return f'<div class="pending"><b>Data pending.</b> {esc(b.get("text", "This section will fill in when the sourced data is ready."))}</div>'


# ---------------------------------------------------------------- visual 1: paired stacked bars
PAL = ["#f2b84b", "#3fb8af", "#8aa4c8", "#e0656f", "#4cc38a", "#b48ead", "#d08770", "#7a8699"]

def b_pairs(P, b):
    """Two stacked bars on the same segments: where revenue comes from vs where profit comes from."""
    keys = {}
    def col(k):
        if k not in keys: keys[k] = PAL[len(keys) % len(PAL)]
        return keys[k]
    cols = []
    for g in b["groups"]:
        pos = [i for i in g["items"] if i["value"] > 0]; tot = sum(i["value"] for i in pos)
        segs = "".join(f'<i style="width:{i["value"] / tot * 100:.3f}%;background:{col(i.get("key", i["label"]))}" title="{esc(i["label"])}: {i["value"] / tot * 100:.1f}%"></i>' for i in pos)
        rows = ""
        for i in g["items"]:
            c = col(i.get("key", i["label"]))
            if i["value"] > 0:
                rows += f'<li><span class="sw" style="background:{c}"></span><span class="pl">{esc(i["label"])}</span><span class="pv num">{money(i["value"] * 1e6, 2)}</span><span class="pp num">{i["value"] / tot * 100:.1f}%</span></li>'
            else:
                rows += f'<li class="neg"><span class="sw" style="background:transparent;border:1px dashed {c}"></span><span class="pl">{esc(i["label"])} (negative, not drawn)</span><span class="pv num">{money(i["value"] * 1e6, 2)}</span><span class="pp num">–</span></li>'
        cols.append(f'<div class="pcol"><h3>{esc(g["title"])}{P.cites(g.get("src"))}</h3><p class="psub">{esc(g.get("sub", ""))}</p><div class="pbar">{segs}</div>'
                    f'<ul class="plist">{rows}</ul><p class="ptot num">{esc(g.get("total_label", "Total"))}: {money(g["total"] * 1e6, 2)}</p></div>')
    call = f'<p class="pcall">{P.rich(b["callout"])}</p>' if b.get("callout") else ""
    note = f'<p class="fine">{P.rich(b["note"])}</p>' if b.get("note") else ""
    return f'<div class="card pairs"><div class="pgrid">{"".join(cols)}</div>{call}{note}</div>'

# ---------------------------------------------------------------- visual 3a: flywheel loop
import math as _m
def b_loop(P, b):
    steps = b["steps"]; n = len(steps)
    CX, CY, RX, RY, BW, BH = 380, 330, 262, 225, 206, 74
    pos = []
    for i in range(n):
        a = -_m.pi / 2 + i * 2 * _m.pi / n
        pos.append((a, CX + RX * _m.cos(a), CY + RY * _m.sin(a)))
    out = ['<defs><marker id="ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0L10,5L0,10z" fill="#f2b84b"/></marker></defs>',
           f'<ellipse cx="{CX}" cy="{CY}" rx="{RX}" ry="{RY}" fill="none" stroke="#1d2531" stroke-width="2"/>']
    # arrows: along the ellipse, from the edge of one box to the edge of the next
    def pt(a): return CX + RX * _m.cos(a), CY + RY * _m.sin(a)
    def inside(a, i):
        x, y = pt(a); bx, by = pos[i][1], pos[i][2]
        return abs(x - bx) < BW / 2 + 8 and abs(y - by) < BH / 2 + 8
    labels = []
    for i in range(n):
        a0, a1 = pos[i][0], pos[i][0] + 2 * _m.pi / n
        s0 = a0
        while inside(s0, i): s0 += .01
        e0 = a1
        while inside(e0, (i + 1) % n): e0 -= .01
        (x0, y0), (x1, y1) = pt(s0), pt(e0)
        out.append(f'<path class="arc" d="M{x0:.1f},{y0:.1f}A{RX},{RY} 0 0 1 {x1:.1f},{y1:.1f}" marker-end="url(#ah)"/>')
        am = (s0 + e0) / 2; lx, ly = pt(am)
        labels.append((lx, ly, steps[i].get("edge", "")))
    for lx, ly, t in labels:
        if not t: continue
        w = len(t) * 8.3 + 18
        out.append(f'<g class="elab"><rect x="{lx - w / 2:.1f}" y="{ly - 13:.1f}" width="{w:.1f}" height="26" rx="13"/><text x="{lx:.1f}" y="{ly + 5:.1f}" text-anchor="middle">{esc(t)}</text></g>')
    for i, st in enumerate(steps):
        _, x, y = pos[i]
        out.append(f'<g class="lnode"><rect x="{x - BW / 2:.1f}" y="{y - BH / 2:.1f}" width="{BW}" height="{BH}" rx="12"/>'
                   f'<text x="{x:.1f}" y="{y - 10:.1f}" text-anchor="middle" class="lt">{i + 1}. {esc(st["title"])}</text>'
                   f'<text x="{x:.1f}" y="{y + 18:.1f}" text-anchor="middle" class="lf">{esc(st["figure"])}</text></g>')
    svg = f'<svg viewBox="0 50 760 560" role="img" aria-label="{esc(b.get("title", "Flywheel"))}">{"".join(out)}</svg>'
    lis = "".join(f'<li><b>{esc(st["title"])}</b> <span class="num">{esc(st["figure"])}</span>. {P.rich(st["text"])}{P.cites(st.get("src"))}</li>' for st in steps)
    note = f'<p class="fine">{P.rich(b["note"])}</p>' if b.get("note") else ""
    return (f'<figure class="loop"><figcaption>{esc(b.get("title", ""))}</figcaption><p class="skhint">Scroll sideways to see the whole loop →</p><div class="loopw">{svg}</div>'
            f'<ol class="looptxt">{lis}</ol>{note}</figure>')

# ---------------------------------------------------------------- visual 3b: holder waffle grid
def b_waffle(P, b):
    cell = b["cell"]; tot = sum(i["value"] for i in b["items"])
    raw = [i["value"] / cell for i in b["items"]]; cnt = [int(r) for r in raw]
    left = round(sum(raw)) - sum(cnt)
    for j in sorted(range(len(raw)), key=lambda j: raw[j] - cnt[j], reverse=True)[:max(left, 0)]: cnt[j] += 1
    N = sum(cnt); COLS = b.get("cols", 25); S, G = 22, 3
    ROWS = -(-N // COLS)
    defs, groups, k = [], [], 0
    for idx, (it, c) in enumerate(zip(b["items"], cnt)):
        colr = PAL[idx % len(PAL)] if "color" not in it else it["color"]
        it["_c"] = colr
        if it.get("est"):
            defs.append(f'<pattern id="h{idx}" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="6" height="6" fill="#161b24"/><rect width="3" height="6" fill="{colr}"/></pattern>')
            fill = f"url(#h{idx})"
        else: fill = colr
        rects = ""
        for _ in range(c):
            r, cc = divmod(k, COLS); k += 1
            rects += f'<rect x="{cc * (S + G)}" y="{r * (S + G)}" width="{S}" height="{S}" rx="3" fill="{fill}"{" stroke=\"" + colr + "\" stroke-width=\"1\"" if it.get("est") else ""}/>'
        groups.append(f'<g class="wg" style="--d:{idx * .12:.2f}s"><title>{esc(it["label"])}: {c} squares</title>{rects}</g>')
    W, H = COLS * (S + G) - G, ROWS * (S + G) - G
    svg = f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{esc(b.get("title", "Holders"))}"><defs>{"".join(defs)}</defs>{"".join(groups)}</svg>'
    unit = b["unit"]; fmtv = lambda v: f'{v:,.{b.get("dec", 0)}f} {unit}'
    rows = ""
    for it, c in zip(b["items"], cnt):
        sw = f'<span class="sw{" hatch" if it.get("est") else ""}" style="--c:{it["_c"]}"></span>'
        est = f' <span class="badge warn">{esc(it.get("est_label", "estimate"))}</span>' if it.get("est") else ""
        rows += f'<tr><td>{sw}{esc(it["label"])}{est}{P.cites(it.get("src"))}</td><td class="r num">{fmtv(it["value"])}</td><td class="r num">{it["value"] / tot * 100:.1f}%</td><td class="r num">{c}</td></tr>'
    note = f'<p class="fine">{P.rich(b["note"])}</p>' if b.get("note") else ""
    return (f'<div class="card waffle"><h3>{esc(b.get("title", ""))}</h3><p class="fine" style="margin:-6px 0 12px"><b>1 square = {b["cell_label"]}</b>. {N} squares in all. Rounded to the nearest square; exact figures in the table. Hatched squares are estimates.</p>'
            f'<div class="wafw">{svg}</div><div class="tw"><table class="v"><thead><tr><th>Holder</th><th class="r">{esc(unit)}</th><th class="r">Share</th><th class="r">Squares</th></tr></thead><tbody>{rows}'
            f'<tr class="tot"><td>{esc(b.get("total_label", "Total shown"))}</td><td class="r num">{fmtv(tot)}</td><td class="r num">100%</td><td class="r num">{N}</td></tr></tbody></table></div>{note}</div>')

BLOCKS = {k[2:]: v for k, v in globals().items() if k.startswith("b_")}

def section(P, sid):
    s = next((x for x in P.e.get("sections", []) if x["id"] == sid), None)
    if s is None:
        if LAUNCH: return ""
        s = {"id": sid, "title": sid.replace("-", " ").title(), "blocks": [{"type": "pending"}]}
    body = "".join(BLOCKS.get(bl["type"], b_pending)(P, bl) for bl in s.get("blocks", []) if P.keep(bl)) or b_pending(P, {})
    lede = f'<p class="slede">{P.rich(s["lede"])}</p>' if s.get("lede") else ""
    head = "" if sid == "ticker" else f'<div class="sh"><h2>{esc(s["title"])}</h2></div>{lede}'
    return f'<section id="{esc(sid)}">{head}{body}</section>'

def sources_html(P):
    lis = []
    for i, (sid, (name, url)) in enumerate(P.src.items(), 1):
        t = f'<a href="{esc(url)}" rel="nofollow noopener" target="_blank">{esc(name)}</a>' if url else esc(name)
        lis.append(f'<li id="src-{esc(sid)}" value="{i}">{t}</li>')
    return f'<section id="sources"><div class="sh"><h2>Sources</h2></div><ol class="sources">{"".join(lis)}</ol><p class="fine">Figures are as published by each source on the dates shown. Derived numbers say so and show their math.</p></section>'

# ---------------------------------------------------------------- pages
def load_entries():
    es = []
    for p in sorted(glob.glob(os.path.join(ROOT, "data", "*.json"))):
        e = json.load(open(p, encoding="utf-8"))
        assert e.get("type") in TYPES, f"{p}: type must be company or commodity"
        assert re.fullmatch(r"[a-z0-9-]+", e["slug"]), f"{p}: bad slug"
        if e.get("live", True): es.append(e)
    return sorted(es, key=lambda e: (e.get("order", 50), e["name"]))

def url_of(e): return f"/{TYPES[e['type']][0]}/{e['slug']}/"

def nav_html(active=None):
    return "".join(f'<a href="/{d}/" class="{"on" if active == d else ""}">{lab}</a>' for d, lab in TYPES.values())

def page(path, title, desc, content, active=None, jump="", page_json="{}", body_class="", jsonld=""):
    base = read("templates/base.html")
    banner = "" if LAUNCH else '<div class="draftbar">DRAFT PREVIEW · not published · for review only</div>\n'
    robots = "" if LAUNCH else '<meta name="robots" content="noindex,nofollow">\n'
    out = fill(base, title=esc(title), description=esc(desc), canonical=BASE_URL + path, robots=robots, root="/",
               css_v=vhash("assets/style.css"), js_v=vhash("assets/clock.js"), nav=nav_html(active), jump=jump,
               content=content, page_json=page_json.replace("</", "<\\/"), draft_banner=banner, body_class=body_class, jsonld=jsonld)
    fp = os.path.join(ROOT, path.lstrip("/"), "index.html") if path.endswith("/") else os.path.join(ROOT, path.lstrip("/"))
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    open(fp, "w", encoding="utf-8").write(out)

def entry_page(e):
    P = Page(e)
    tpl = read(f"templates/{e.get('template', e['type'])}.html")
    body = re.sub(r"\{\{section:([\w-]+)\}\}", lambda m: section(P, m.group(1)), tpl)
    body = fill(body, h1=esc(e["title"]), tagline=esc(e.get("tagline", "")), as_of=esc(e.get("as_of", "")),
                ticker_symbol=esc(e.get("ticker_symbol", "")), symbol=esc(e.get("symbol", "")), sources=sources_html(P))
    ids = re.findall(r'<section id="([\w-]+)"><div class="sh"><h2>([^<]+)</h2>', body)
    jump = '<nav class="jump">' + "".join(f'<a href="#{i}">{t}</a>' for i, t in ids) + "</nav>"
    tickers = [bl for s in e.get("sections", []) for bl in s["blocks"] if bl["type"] == "ticker"]
    pj = json.dumps({"counters": [dict(id=c["id"], unit=c["unit"], rate=c["annual"] / t["period_seconds"]) for t in tickers for c in t["counters"]] + P.live})
    url = BASE_URL + url_of(e); hub = TYPES[e["type"]]
    about = ({"@type": "Corporation", "name": e.get("legal_name", e["name"]), "tickerSymbol": e["ticker_symbol"]} if e.get("ticker_symbol") else {"@type": "Thing", "name": e["name"]})
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebPage", "@id": url + "#page", "url": url, "name": f'{e["title"]} | Flywheel Clock', "description": e["description"], "inLanguage": "en",
         "isPartOf": {"@type": "WebSite", "name": "Flywheel Clock", "url": BASE_URL + "/"}, "about": about,
         "publisher": {"@type": "Organization", "name": "Hypergame", "url": BASE_URL + "/"}, "dateModified": date.today().isoformat()},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Flywheel Clock", "item": BASE_URL + "/"},
            {"@type": "ListItem", "position": 2, "name": hub[1], "item": f"{BASE_URL}/{hub[0]}/"},
            {"@type": "ListItem", "position": 3, "name": e["name"], "item": url}]}]}
    jl = '<script type="application/ld+json">' + json.dumps(ld).replace("</", "<\\/") + '</script>\n'
    page(url_of(e), f'{e["title"]} | Flywheel Clock', e["description"], body, active=hub[0], jump=jump, page_json=pj, jsonld=jl)

def card(e):
    cs = e.get("card_stat", {})
    return (f'<a class="ecard" href="{url_of(e)}"><div class="et">{esc(e["name"])}<span>{esc(e.get("ticker_symbol") or e.get("symbol") or "")}</span></div>'
            f'<div class="es"><span class="l">{esc(cs.get("label", ""))}</span><span class="num v">{esc(cs.get("value", ""))}</span><span class="n">{esc(cs.get("note", ""))}</span></div>'
            f'<p>{esc(e.get("tagline", ""))}</p><span class="go">Open →</span></a>')

def build():
    for d, _ in TYPES.values(): shutil.rmtree(os.path.join(ROOT, d), ignore_errors=True)
    es = load_entries()
    for e in es: entry_page(e)
    groups = ""
    for t, (d, lab) in TYPES.items():
        mine = [e for e in es if e["type"] == t]
        if not mine: continue        # no "coming soon" sections: only live entries are listed
        cards = "".join(card(e) for e in mine)
        groups += f'<section><div class="sh"><h2><a href="/{d}/">{lab}</a></h2></div><div class="ecards">{cards}</div></section>'
        page(f"/{d}/", f"{lab} | Flywheel Clock", f"How the biggest {lab.lower()} make, move and hold money, with live clocks and sourced data.",
             f'<h1>{lab}</h1><div class="ecards">{cards}</div>', active=d)
    page("/", "Flywheel Clock: how big companies and commodities really work",
         "Live money clocks for the biggest companies and commodities: where the money comes from, where it goes, and the decisions and history behind it.",
         fill(read("templates/home.html"), groups=groups), body_class="home",
         jsonld='<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@type": "WebSite", "name": "Flywheel Clock", "url": BASE_URL + "/",
                "description": "Live money clocks for the biggest companies and commodities, with sourced data.",
                "publisher": {"@type": "Organization", "name": "Hypergame", "url": BASE_URL + "/"}}) + '</script>\n')
    page("/privacy/", "Privacy | Flywheel Clock", "What Flywheel Clock collects when you visit: no accounts, no forms, and privacy-focused analytics from Cloudflare.", read("templates/privacy.html"))
    page("/404.html", "Not found | Flywheel Clock", "Page not found.", '<h1>Page not found</h1><p><a href="/">Back to the homepage</a></p>')
    urls = ["/"] + [f"/{d}/" for t, (d, _) in TYPES.items() if any(e["type"] == t for e in es)] + [url_of(e) for e in es] + ["/privacy/"]
    today = date.today().isoformat()
    sm = "".join(f"<url><loc>{BASE_URL}{u}</loc><lastmod>{today}</lastmod></url>" for u in urls)
    open(os.path.join(ROOT, "sitemap.xml"), "w").write(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>\n')
    open(os.path.join(ROOT, "robots.txt"), "w").write(("User-agent: *\nAllow: /\n" if LAUNCH else "User-agent: *\nDisallow: /\n") + f"Sitemap: {BASE_URL}/sitemap.xml\n")
    print(f"built {len(es)} entries ({'launch' if LAUNCH else 'draft'}):", ", ".join(url_of(e) for e in es))

if __name__ == "__main__":
    build()
