# -*- coding: utf-8 -*-
"""Regenerate the profile SVGs.

Edit COLS / PANEL / THEMES below and run `python assets/build.py`; both themes are
emitted from this single source so they cannot drift apart.

Type is IBM Plex Sans / IBM Plex Mono (SIL OFL 1.1). GitHub loads these SVGs via
<img>, which blocks external resources, so each file carries its own webfont —
subsetted per file and per weight to exactly the glyphs that file renders.
Originals are cached in .fontcache/ (gitignored) and fetched on first run.
"""
import io, os, re, base64, urllib.request
from fontTools import subset

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, ".fontcache")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"}

# (family, weight) -> Google Fonts family name
FONTS = {
    ("sans", 400): "IBM+Plex+Sans", ("sans", 600): "IBM+Plex+Sans",
    ("mono", 400): "IBM+Plex+Mono", ("mono", 500): "IBM+Plex+Mono",
}
FALLBACK = {
    "sans": 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
    "mono": 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
}
# css class -> (family, weight, size, letter-spacing, colour token)
TYPE = {
    "n": ("sans", 600, 46,   -0.6, "fg1"),
    "r": ("sans", 400, 15,    0,   "fg3"),
    "l": ("mono", 500,  9.5,  1.8, "fg4"),
    "v": ("sans", 400, 13.5,  0,   "fg2"),
    "m": ("mono", 400, 12,    0.2, "fg2"),
    "i": ("mono", 500,  9.5,  0.6, "fg4"),
    "s": ("mono", 400,  8,    1.2, "fg4"),
}

THEMES = {
    "light": dict(fg1="#1f2328", fg2="#424a53", fg3="#6e7781", fg4="#9198a1",
                  line1="#d1d9e0", line2="#e4e8ec", accent="#9a6700", star="#57606a"),
    "dark":  dict(fg1="#e6edf3", fg2="#b9c1ca", fg3="#7d8590", fg4="#636c76",
                  line1="#30363d", line2="#21262d", accent="#d29922", star="#8b949e"),
}

# Virgo, schematic: one chain from Vindemiatrix down to Spica, plus a branch.
STARS = [(824, 10, 1.6), (786, 26, 1.35), (744, 44, 1.85),
         (700, 68, 1.4), (800, 58, 1.15), (856, 44, 1.3)]
SPICA = (642, 92, 2.7)
EDGES = [(824, 10, 786, 26), (786, 26, 744, 44), (744, 44, 700, 68),
         (700, 68, 642, 92), (744, 44, 800, 58), (800, 58, 856, 44)]

COLS = [
    ("BASED IN",  [("v", "Shanghai, CN"), ("m", "31.02°N  121.43°E")]),
    ("FOCUS",     [("v", "Systems and tooling"), ("v", "Local LLM inference")]),
    ("OBSERVING", [("v", "Spica · α Virginis"), ("m", "mag 0.97 · 250 ly")]),
]
# (label, columns each item spans, items)
PANEL = [
    ("CURRENTLY LEARNING", 1, ["C and C++", "Python", "Node.js", "LLM deployment"]),
    ("OFF THE CLOCK",      1, ["Arknights", "Arknights: Endfield", "Counter-Strike 2", "manosaba"]),
    ("REACH ME",           2, ["misterrabbit0w0@gmail.com", "misterrabbit0w0@qq.com"]),
]


def fetch(fam, weight):
    """Original woff2 for one family/weight, cached on disk."""
    path = os.path.join(CACHE, f"{fam.replace('+', '')}-{weight}.woff2")
    if os.path.exists(path):
        return path
    os.makedirs(CACHE, exist_ok=True)
    css = urllib.request.urlopen(urllib.request.Request(
        f"https://fonts.googleapis.com/css2?family={fam}:wght@{weight}&display=swap",
        headers=UA)).read().decode()
    block = re.search(r'/\*\s*latin\s*\*/\s*@font-face\s*\{(.*?)\}', css, re.S)
    url = re.search(r'url\((https[^)]+\.woff2)\)', block.group(1)).group(1)
    io.open(path, "wb").write(urllib.request.urlopen(url).read())
    return path


def face(key, chars):
    """One @font-face rule carrying a subset of exactly `chars`."""
    fam, weight = key
    src, dst = fetch(FONTS[key], weight), os.path.join(CACHE, "out.woff2")
    subset.main([src, "--text=" + "".join(sorted(chars)), "--output-file=" + dst,
                 "--flavor=woff2", "--layout-features=", "--no-hinting",
                 "--desubroutinize", "--drop-tables+=GSUB,GPOS"])
    b64 = base64.b64encode(io.open(dst, "rb").read()).decode()
    os.remove(dst)
    return (f"@font-face{{font-family:{fam};font-style:normal;font-weight:{weight};"
            f"src:url(data:font/woff2;base64,{b64}) format('woff2')}}")


def esc(s):
    return "".join(c if ord(c) < 128 and c not in "<>&" else f"&#{ord(c)};" for c in s)


class Doc:
    """Collects markup and, alongside it, which glyphs each weight actually needs."""

    def __init__(self, w, h, label):
        self.w, self.h, self.label = w, h, label
        self.body, self.used = [], {}

    def text(self, cls, x, y, s, fill=None):
        fam, weight = TYPE[cls][0], TYPE[cls][1]
        self.used.setdefault((fam, weight), set()).update(s)
        extra = f' fill="{fill}"' if fill else ""
        self.body.append(f'  <text class="{cls}" x="{x}" y="{y}"{extra}>{esc(s)}</text>')

    def add(self, markup):
        self.body.append(markup)

    def render(self, t):
        css = [face(k, v) for k, v in sorted(self.used.items())]
        for cls, (fam, weight, size, tracking, tok) in TYPE.items():
            if (fam, weight) not in self.used:
                continue
            css.append(f".{cls}{{font-family:{fam},{FALLBACK[fam]};font-weight:{weight};"
                       f"font-size:{size}px;letter-spacing:{tracking}px;fill:{t[tok]}}}")
        return "\n".join([
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
            f'viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{self.label}">',
            "  <defs><style>" + "".join(css) + "</style></defs>",
            *self.body, "</svg>"]) + "\n"


def header(t):
    d = Doc(880, 226,
            "MisterRabbit0w0 &#8212; undergraduate at Shanghai Jiao Tong University. "
            "Based in Shanghai; focused on systems, tooling and local LLM inference.")
    d.add(f'  <defs><radialGradient id="glow" cx="50%" cy="50%" r="50%">'
          f'<stop offset="0" stop-color="{t["accent"]}" stop-opacity=".30"/>'
          f'<stop offset="1" stop-color="{t["accent"]}" stop-opacity="0"/>'
          f'</radialGradient></defs>')
    d.add(f'  <g stroke="{t["line1"]}" stroke-width="1" fill="none">')
    for x1, y1, x2, y2 in EDGES:
        d.add(f'    <path d="M{x1} {y1} L{x2} {y2}"/>')
    d.add("  </g>")
    d.add(f'  <g fill="{t["star"]}" opacity=".9">')
    for x, y, r in STARS:
        d.add(f'    <circle cx="{x}" cy="{y}" r="{r}"/>')
    d.add("  </g>")
    sx, sy, sr = SPICA
    d.add(f'  <circle cx="{sx}" cy="{sy}" r="16" fill="url(#glow)"/>')
    d.add(f'  <circle cx="{sx}" cy="{sy}" r="{sr}" fill="{t["accent"]}"/>')
    d.text("s", sx + 8, sy + 3.5, "α", fill=t["accent"])

    d.text("n", 0, 54, "MisterRabbit0w0")
    d.text("r", 2, 82, "Undergraduate at Shanghai Jiao Tong University")

    d.add(f'  <path d="M0 124.5 H880" stroke="{t["line1"]}" stroke-width="1"/>')
    for gx in (290, 590):
        d.add(f'  <path d="M{gx}.5 136 V196" stroke="{t["line2"]}" stroke-width="1"/>')
    for x, (label, rows) in zip([0, 300, 600], COLS):
        d.text("l", x + 1, 149, label)
        for i, (cls, val) in enumerate(rows):
            d.text(cls, x + 1, 174 + i * 20, val)
    return d


def panel(t):
    d = Doc(880, 288,
            "Currently learning: C and C++, Python, Node.js, LLM deployment. "
            "Off the clock: Arknights, Arknights Endfield, Counter-Strike 2, manosaba. "
            "Reach me at misterrabbit0w0@gmail.com or misterrabbit0w0@qq.com.")
    d.add(f'  <path d="M0 0.5 H880" stroke="{t["line1"]}" stroke-width="1"/>')
    for gi, (label, span, items) in enumerate(PANEL):
        top = 32 + gi * 88
        d.text("l", 1, top + 12, label)
        d.add(f'  <path d="M0 {top + 26.5} H880" stroke="{t["line1"]}" stroke-width="1"/>')
        for i, item in enumerate(items):
            x = i * 225 * span
            if i:
                d.add(f'  <path d="M{x - 10}.5 {top + 38} V{top + 60}" '
                      f'stroke="{t["line2"]}" stroke-width="1"/>')
            d.text("i", x + 1, top + 52, f"{i + 1:02d}")
            d.text("v", x + 26, top + 52, item)
    return d


PREVIEW = """<!doctype html>
<meta charset="utf-8"><title>profile preview</title>
<style>
  body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans",
         Helvetica,Arial,sans-serif; }}
  .pane {{ padding:44px 0; }}
  .light {{ background:#fff; }}  .dark {{ background:#0d1117; }}
  .readme {{ width:875px; margin:0 auto; font-size:16px; line-height:1.5; }}
  .light .readme {{ color:#1f2328; }}  .dark .readme {{ color:#e6edf3; }}
  .readme p {{ margin:0 0 16px; }}
  .readme img {{ max-width:100%; vertical-align:middle; }}
  .light .readme a {{ color:#0969da; }}  .dark .readme a {{ color:#4493f8; }}
  .readme a {{ text-decoration:none; }}
  .tag {{ font:11px ui-monospace,monospace; letter-spacing:2px; opacity:.4;
         width:875px; margin:0 auto 18px; }}
  .dark .tag {{ color:#e6edf3; }}
</style>
<div class="pane light"><p class="tag">LIGHT &#183; as rendered on github.com</p>
  <div class="readme">{light}</div></div>
<div class="pane dark"><p class="tag">DARK &#183; as rendered on github.com</p>
  <div class="readme">{dark}</div></div>
"""


def build_preview():
    """Render README.md side by side in both themes, so the page never drifts
    from what GitHub will actually show."""
    md = io.open(os.path.join(os.path.dirname(HERE), "README.md"), encoding="utf-8").read()
    picts = re.findall(r"<picture>.*?</picture>", md, re.S)
    out = {}
    for theme in ("light", "dark"):
        body = md
        for block in picts:
            if theme == "dark":
                url = re.search(r'srcset="([^"]+)"', block).group(1)
            else:
                url = re.search(r'<img[^>]*\ssrc="([^"]+)"', block).group(1)
            alt = re.search(r'alt="([^"]*)"', block)
            # must match the img's own attribute — card URLs contain "card_width="
            wide = ' width="100%"' if re.search(r'<img[^>]*\swidth="100%"', block) else ""
            body = body.replace(block, f'<img src="{url.replace("./assets/", "./")}" '
                                       f'alt="{alt.group(1) if alt else ""}"{wide}>')
        chunks = []
        for para in re.split(r"\n\s*\n", body.strip()):
            para = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", para)
            para = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', para)
            chunks.append(para if para.lstrip().startswith("<") else f"<p>{para}</p>")
        out[theme] = "\n".join(chunks)
    path = os.path.join(HERE, "preview.html")
    io.open(path, "w", encoding="utf-8", newline="\n").write(PREVIEW.format(**out))
    return path


if __name__ == "__main__":
    for name, theme in THEMES.items():
        for kind, fn in (("header", header), ("panel", panel)):
            path = os.path.join(HERE, f"{kind}-{name}.svg")
            io.open(path, "w", encoding="utf-8", newline="\n").write(fn(theme).render(theme))
            print(f"wrote {kind}-{name}.svg  {os.path.getsize(path) / 1024:5.1f}K")
    print("wrote " + os.path.basename(build_preview()) + "   (open it to check both themes)")
