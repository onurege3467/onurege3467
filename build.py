"""Profil README'sini ve SVG varlıklarını config.json'dan üretir."""
import json
import textwrap
from html import escape
from pathlib import Path

ROOT = Path(__file__).parent
CFG = json.loads((ROOT / "config.json").read_text())
FONT = "-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
DISPLAY = "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"


def header(t):
    h = CFG["header"]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 840 176" role="img" aria-label="{escape(h['name'])}">
<style>
  g {{ animation: in .6s cubic-bezier(.2,.8,.2,1) both; }}
  @keyframes in {{ from {{ opacity: 0; transform: translateY(6px); }} }}
  @media (prefers-reduced-motion: reduce) {{ g {{ animation: none; }} }}
</style>
<g>
  <text x="0" y="72" font-family="{DISPLAY}" font-size="56" font-weight="700" letter-spacing="-1.4" fill="{t['fg']}">{escape(h['name'])}</text>
  <text x="1" y="118" font-family="{DISPLAY}" font-size="20" font-weight="500" letter-spacing="-0.2" fill="{t['fg']}">{escape(h['tagline'])}</text>
  <text x="1" y="150" font-family="{FONT}" font-size="15" letter-spacing="0" fill="{t['muted']}">{escape(h['sub'])}</text>
</g>
</svg>"""


def card(t, name, desc, lang):
    c, m = CFG["card"], 8  # m: gölge için kenar payı
    w, h, p = c["w"], c["h"], c["pad"]
    lines = textwrap.wrap(desc, c["wrap"])[:2]
    desc_svg = "".join(
        f'<text x="{m+p}" y="{m+68+i*19}" font-family="{FONT}" font-size="13.5" fill="{t["muted"]}">{escape(l)}</text>'
        for i, l in enumerate(lines))
    color = CFG["langColors"].get(lang, t["faint"])
    shadow = (f'<filter id="s" x="-10%" y="-10%" width="120%" height="140%"><feDropShadow dx="0" dy="2" stdDeviation="4" '
              f'flood-color="#000" flood-opacity="{t["shadow"]}"/></filter>') if t["shadow"] else ""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w+2*m} {h+2*m}" role="img" aria-label="{escape(name)}: {escape(desc)}">
<defs>{shadow}<linearGradient id="e" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t['edge']}"/><stop offset=".25" stop-color="{t['border']}"/></linearGradient></defs>
<rect x="{m+.5}" y="{m+.5}" width="{w-1}" height="{h-1}" rx="{c['radius']}" fill="{t['card']}" stroke="url(#e)" {'filter="url(#s)"' if shadow else ''}/>
<text x="{m+p}" y="{m+42}" font-family="{DISPLAY}" font-size="17" font-weight="600" letter-spacing="-0.2" fill="{t['fg']}">{escape(name)}</text>
<text x="{m+w-p}" y="{m+42}" text-anchor="end" font-family="{FONT}" font-size="15" fill="{t['faint']}">↗</text>
{desc_svg}
<circle cx="{m+p+5}" cy="{m+h-p-4}" r="5" fill="{color}"/>
<text x="{m+p+16}" y="{m+h-p}" font-family="{FONT}" font-size="12" letter-spacing="0.1" fill="{t['muted']}">{escape(lang)}</text>
</svg>"""


def pic(slug, alt, width, href=None):
    img = (f'<picture><source media="(prefers-color-scheme: dark)" srcset="assets/{slug}-dark.svg">'
           f'<img src="assets/{slug}-light.svg" alt="{escape(alt)}" width="{width}"></picture>')
    return f'<a href="{href}">{img}</a>' if href else img


def main():
    out = ROOT / "assets"
    out.mkdir(exist_ok=True)
    user, h, f = CFG["user"], CFG["header"], CFG["footer"]
    for mode, t in CFG["themes"].items():
        (out / f"header-{mode}.svg").write_text(header(t))
        for s in CFG["sections"]:
            for name, desc, lang in s["repos"]:
                (out / f"{name.lower()}-{mode}.svg").write_text(card(t, name, desc, lang))

    md = [pic("header", f"{h['name']}. {h['tagline']} {h['sub']}", "100%"), ""]
    for s in CFG["sections"]:
        md += [f"### {s['title']}", "", "<p>"]
        md += [pic(n.lower(), f"{n} — {d}", "400", f"https://github.com/{user}/{n}") for n, d, _ in s["repos"]]
        md += ["</p>", ""]
    md += ["---", "", f"<sub>{escape(f['stack'])}</sub>", "",
           f"{f['note']}  ", f"[{f['site'].split('//')[1].removeprefix('www.')}]({f['site']}) · [{f['email']}](mailto:{f['email']})", ""]
    (ROOT / "README.md").write_text("\n".join(md))


if __name__ == "__main__":
    main()
