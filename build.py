"""Profil README'sini ve SVG varlıklarını config.json'dan üretir."""
import json
import re
import textwrap
from html import escape
from pathlib import Path

ROOT = Path(__file__).parent
CFG = json.loads((ROOT / "config.json").read_text())
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif"


def style(t):
    # Ortak stil tek yerde: her <text>'te font/renk tekrarlanmaz. Animasyon yok, ilk karede tam görünür.
    return (f"<style>text{{font-family:{FONT};fill:{t['muted']}}}.f{{fill:{t['fg']}}}.x{{fill:{t['faint']}}}"
            ".b{font-weight:600;letter-spacing:-.2px}.i{fill:" + t["muted"] + "}</style>")


def header(t):
    h = CFG["header"]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 840 176" role="img" aria-label="{escape(h["name"])}">{style(t)}'
            f'<text x="0" y="72" class="f" font-size="56" font-weight="700" letter-spacing="-1.4">{escape(h["name"])}</text>'
            f'<text x="1" y="118" class="f" font-size="20" font-weight="500" letter-spacing="-.2">{escape(h["tagline"])}</text>'
            f'<text x="1" y="150" font-size="15">{escape(h["sub"])}</text></svg>')


def card(t, name, desc, lang, url=None):
    c, m = CFG["card"], 8  # m: gölge için kenar payı
    w, h, p = c["w"], c["h"], c["pad"]
    lines = textwrap.wrap(desc, c["wrap"])[:2]
    body = "".join(f'<text x="{m+p}" y="{m+68+i*19}" font-size="13.5">{escape(l)}</text>' for i, l in enumerate(lines))
    shadow = (f'<filter id="s" y="-10%" height="140%"><feDropShadow dy="2" stdDeviation="4" flood-opacity="{t["shadow"]}"/></filter>'
              if t["shadow"] else "")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w+2*m} {h+2*m}" role="img" aria-label="{escape(name)}">{style(t)}'
            f'<defs>{shadow}<linearGradient id="e" x2="0" y2="1"><stop stop-color="{t["edge"]}"/><stop offset=".25" stop-color="{t["border"]}"/></linearGradient></defs>'
            f'<rect x="{m+.5}" y="{m+.5}" width="{w-1}" height="{h-1}" rx="{c["radius"]}" fill="{t["card"]}" stroke="url(#e)"{" filter=\"url(#s)\"" if shadow else ""}/>'
            f'<text x="{m+p}" y="{m+42}" class="f b" font-size="17">{escape(name)}</text>'
            f'<text x="{m+w-p}" y="{m+42}" class="x" text-anchor="end" font-size="15">↗</text>{body}'
            f'<circle cx="{m+p+5}" cy="{m+h-p-4}" r="5" fill="{CFG["langColors"].get(lang, t["faint"])}"/>'
            f'<text x="{m+p+16}" y="{m+h-p}" font-size="12">{escape(lang)}</text>'
            + (f'<text x="{m+w-p}" y="{m+h-p}" class="x" text-anchor="end" font-size="12">npm</text>' if url and "npmjs.com" in url else "")
            + '</svg>')


NUM = re.compile(r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?")


def compact_path(d):
    """Path sayılarını 1 ondalığa yuvarlar (24'lük ikon 16px'te çizilir, fark görünmez). Arc bayrakları korunur."""
    out, i, cmd, idx = [], 0, "", 0
    while i < len(d):
        ch = d[i]
        if ch.isalpha():
            cmd, idx = ch, 0
            out.append(ch)
            i += 1
        elif ch in " ,\t\n":
            i += 1
        elif cmd in "aA" and idx % 7 in (3, 4):  # bayrak: tek karakter, sayı gibi ayrılır
            if out and not out[-1].isalpha():
                out.append(" ")
            out.append(ch)
            idx += 1
            i += 1
        else:
            m = NUM.match(d, i)
            v = f"{round(float(m.group()), 1):.1f}".rstrip("0").rstrip(".")
            v = "0" if v in ("-0", "") else v.replace("0.", ".", 1) if v.lstrip("-").startswith("0.") else v
            if out and not out[-1].isalpha() and not v.startswith("-"):
                out.append(" ")
            out.append(v)
            idx += 1
            i = m.end()
    return "".join(out)


def icon(name):
    svg = (ROOT / CFG["iconDir"] / f"{CFG['icons'][name]}.svg").read_text()
    rule = ' fill-rule="evenodd"' if "evenodd" in svg else ""
    return f'<path{rule} d="{compact_path(re.search(r' d="([^"]+)"', svg).group(1))}"/>'


def flow(items):
    """İkon + ad çiplerini kart genişliğine sığacak satırlara dizer (metin genişliği tahmini)."""
    c = CFG["card"]
    inner = c["w"] - 2 * c["pad"]
    rows, row, x = [], [], 0
    for it in items:
        wd = c["chipIcon"] + c["chipGap"] + len(it) * c["chipFont"] * c["chipCharW"]
        if row and x + wd > inner:
            rows.append(row)
            row, x = [], 0
        row.append((it, x))
        x += wd + c["chipSpace"]
    return rows + [row]


def stack_height():
    c = CFG["card"]
    return 58 + max(len(flow(i)) for _, i in CFG["stack"]["groups"]) * c["chipLine"] + 10


def stack_card(t, title, items):
    c, m = CFG["card"], 8
    w, h, p, s = c["w"], stack_height(), c["pad"], c["chipIcon"] / 24
    chips = []
    for r, row in enumerate(flow(items)):
        y = m + 58 + r * c["chipLine"]
        for it, x in row:
            chips.append(f'<g class="i" transform="translate({m+p+x:g} {y}) scale({s:.3g})">{icon(it)}</g>'
                         f'<text x="{m+p+x+c["chipIcon"]+c["chipGap"]:g}" y="{y+12.5:g}" class="f" font-size="{c["chipFont"]}">{escape(it)}</text>')
    shadow = (f'<filter id="s" y="-10%" height="140%"><feDropShadow dy="2" stdDeviation="4" flood-opacity="{t["shadow"]}"/></filter>'
              if t["shadow"] else "")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w+2*m} {h+2*m}" role="img" aria-label="{escape(title)}">{style(t)}'
            f'<defs>{shadow}<linearGradient id="e" x2="0" y2="1"><stop stop-color="{t["edge"]}"/><stop offset=".25" stop-color="{t["border"]}"/></linearGradient></defs>'
            f'<rect x="{m+.5}" y="{m+.5}" width="{w-1}" height="{h-1}" rx="{c["radius"]}" fill="{t["card"]}" stroke="url(#e)"{" filter=\"url(#s)\"" if shadow else ""}/>'
            f'<text x="{m+p}" y="{m+38}" class="f b" font-size="17">{escape(title)}</text>{"".join(chips)}</svg>')


def slug(name):
    return name.lower().replace(" ", "-").replace("&", "and")


def pic(slug, alt, width, href=None):
    # Mutlak raw URL: göreli yol github.com/.../raw üzerinden 302 yönlendirmesiyle geliyor, bu bir tur tasarruf eder.
    base = CFG["assetBase"]
    img = (f'<picture><source media="(prefers-color-scheme: dark)" srcset="{base}{slug}-dark.svg">'
           f'<img src="{base}{slug}-light.svg" alt="{escape(alt)}" width="{width}"></picture>')
    return f'<a href="{href}">{img}</a>' if href else img


def button_width(label):
    b = CFG["button"]
    return round(2 * b["padX"] + b["icon"] + b["gap"] + len(label) * b["font"] * b["charW"])


def button(t, label, icon_name, primary):
    b = CFG["button"]
    w, h = button_width(label), b["h"]
    bg, fg = (t["btnBg"], t["btnFg"]) if primary else (t["card"], t["fg"])
    stroke = "" if primary else ' stroke="url(#e)"'
    paths = "".join(f'<path d="{d}"/>' for d in re.findall(r' d="([^"]+)"', (ROOT / CFG["iconDir"] / f"{icon_name}.svg").read_text()))
    y0 = (h - b["icon"]) / 2
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{escape(label)}">'
            f'<style>text{{font-family:{FONT};font-weight:500;fill:{fg}}}</style>'
            f'<defs><linearGradient id="e" x2="0" y2="1"><stop stop-color="{t["edge"]}"/><stop offset=".25" stop-color="{t["border"]}"/></linearGradient></defs>'
            f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="{(h-1)/2}" fill="{bg}"{stroke}/>'
            f'<g transform="translate({b["padX"]} {y0:g}) scale({b["icon"]/24:.3g})" fill="none" stroke="{fg}" stroke-width="1.8" '
            f'stroke-linecap="round" stroke-linejoin="round">{paths}</g>'
            f'<text x="{b["padX"]+b["icon"]+b["gap"]}" y="{h/2+5:g}" font-size="{b["font"]}">{escape(label)}</text></svg>')


def main():
    out = ROOT / "assets"
    out.mkdir(exist_ok=True)
    user, h, ct = CFG["user"], CFG["header"], CFG["contact"]
    for mode, t in CFG["themes"].items():
        (out / f"header-{mode}.svg").write_text(header(t))
        for s in CFG["sections"]:
            for name, desc, lang, *url in s["repos"]:
                (out / f"{name.lower()}-{mode}.svg").write_text(card(t, name, desc, lang, *url))
        for title, items in CFG["stack"]["groups"]:
            (out / f"stack-{slug(title)}-{mode}.svg").write_text(stack_card(t, title, items))
        for btn in ct["buttons"]:
            (out / f"btn-{btn['icon']}-{mode}.svg").write_text(button(t, btn["label"], btn["icon"], btn["primary"]))

    md = [pic("header", f"{h['name']}. {h['tagline']} {h['sub']}", "100%"), ""]
    st = CFG["stack"]
    md += [f"### {st['title']}", "", "<p>"]
    md += [pic(f"stack-{slug(g)}", f"{g}: {', '.join(items)}", "400") for g, items in st["groups"]]
    md += ["</p>", ""]
    for s in CFG["sections"]:
        md += [f"### {s['title']}", "", "<p>"]
        md += [pic(n.lower(), f"{n} ({l}{', npm' if u else ''}) — {d}", "400", u[0] if u else f"https://github.com/{user}/{n}")
               for n, d, l, *u in s["repos"]]
        md += ["</p>", ""]
    md += [f"### {ct['title']}", "", ct["note"], "", '<p align="center">']
    md += [pic(f"btn-{b['icon']}", b["alt"], str(button_width(b["label"])), b["href"]) for b in ct["buttons"]]
    md += ["</p>", ""]
    (ROOT / "README.md").write_text("\n".join(md))


if __name__ == "__main__":
    main()
