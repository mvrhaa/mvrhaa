from __future__ import annotations

import datetime as dt
import html
import pathlib
from zoneinfo import ZoneInfo

FIRST_NAME = "Ruslan"
LAST_NAME = "Murha"
HANDLE = "mvrha"
TIMEZONE = "Europe/Warsaw"
OUT_DIR = pathlib.Path(__file__).resolve().parent / "assets"

FONT = ("ui-monospace,'SF Mono',SFMono-Regular,Menlo,Consolas,"
        "'Liberation Mono','DejaVu Sans Mono',monospace")
COL = {
    "bg": "#0c0d10", "bar": "#15171c", "sep": "#23272e", "border": "#2c3139",
    "title": "#7d8590", "text": "#d4cfc5", "dim": "#6b7079", "cmd": "#f2eee6",
    "user": "#f0a35e", "host": "#d9b27c", "path": "#8fb3d9", "sym": "#7d8590",
    "cursor": "#f0a35e",
}


def esc(s: str) -> str:
    return html.escape(s, quote=False)


def text_el(x, y, segs, cw, attrs=""):
    n = sum(len(t) for t, _ in segs)
    body = "".join(f'<tspan class="{c}">{esc(t)}</tspan>' if c else esc(t) for t, c in segs)
    return (f'<text x="{x:.1f}" y="{y:.1f}" textLength="{n * cw:.1f}" '
            f'lengthAdjust="spacingAndGlyphs"{attrs}>{body}</text>')


def window(x, y, w, h, title):
    r = 10
    lights = "".join(f'<circle cx="{x + cx}" cy="{y + BAR / 2}" r="5.5" fill="{c}"/>'
                     for cx, c in ((18, "#ff5f57"), (36, "#febc2e"), (54, "#28c840")))
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{COL["bg"]}"/>'
            f'<path d="M{x + r} {y}h{w - 2 * r}a{r} {r} 0 0 1 {r} {r}v{BAR - r}h{-w}v{r - BAR}'
            f'a{r} {r} 0 0 1 {r} {-r}z" fill="{COL["bar"]}"/>'
            f'<path d="M{x} {y + BAR + 0.5}h{w}" stroke="{COL["sep"]}"/>' + lights
            + f'<text x="{x + w / 2}" y="{y + 19}" text-anchor="middle" class="wt">{esc(title)}</text>')


def window_border(x, y, w, h):
    return (f'<rect x="{x + 0.5}" y="{y + 0.5}" width="{w - 1}" height="{h - 1}" rx="9.5" '
            f'fill="none" stroke="{COL["border"]}"/>')


def prompt(path="~"):
    return [(HANDLE, "cu"), ("@", "cs"), ("github", "ch"), (" ", None), (path, "cp"), (" % ", "cs")]


LEFT_W, RIGHT_W, WIN_H, MARGIN, GAP, BAR, PAD = 350, 484, 330, 6, 14, 30, 14
TFS, TCW, TLH = 12.2, 7.35, 17.4


def build() -> str:
    W, H = MARGIN * 2 + LEFT_W + GAP + RIGHT_W, MARGIN * 2 + WIN_H
    lx, ly = MARGIN, MARGIN
    rx, ry = MARGIN + LEFT_W + GAP, MARGIN

    tx, y = rx + PAD, ry + BAR + 10
    try:
        now = dt.datetime.now(ZoneInfo(TIMEZONE))
    except Exception:
        now = dt.datetime.now()
    term = [text_el(tx, y + TLH * 0.74, [(f"Last login: {now:%a %b %d %H:%M:%S} on ttys001", "cm")], TCW)]
    y += TLH
    p = prompt()
    plen = sum(len(s) for s, _ in p)
    term.append(text_el(tx, y + TLH * 0.74, p, TCW)
                + f'<rect class="cur" x="{tx + plen * TCW:.1f}" y="{y + 2:.1f}" width="{TCW:.1f}" '
                  f'height="{TLH - 3:.1f}" fill="{COL["cursor"]}"/>')

    body = [
        window(rx, ry, RIGHT_W, WIN_H, f"{HANDLE}@github: ~ — zsh — 80×24"),
        f'<g class="t" clip-path="url(#clipT)">{"".join(term)}</g>',
        window_border(rx, ry, RIGHT_W, WIN_H),
        window(lx, ly, LEFT_W, WIN_H, "eye — ascii"),
        window_border(lx, ly, LEFT_W, WIN_H),
    ]

    classes = {"cu": COL["user"], "cs": COL["sym"], "ch": COL["host"], "cp": COL["path"], "cm": COL["dim"]}
    style = (f"text{{font-family:{FONT};white-space:pre;fill:{COL['text']}}}"
             f".t text{{font-size:{TFS}px}}"
             f".wt{{font-size:12px!important;fill:{COL['title']}!important;white-space:normal}}"
             + "".join(f".{k}{{fill:{v}}}" for k, v in classes.items())
             + ".cur{animation:bl 1.1s step-end infinite}@keyframes bl{0%{opacity:1}50%{opacity:0}}")
    clip = (f'<clipPath id="clipT"><rect x="{rx}" y="{ry + BAR + 1}" width="{RIGHT_W}" '
            f'height="{WIN_H - BAR - 1}" rx="10"/></clipPath>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
            f'xml:space="preserve" role="img" aria-label="{esc(FIRST_NAME)} {esc(LAST_NAME)} — terminal">'
            f'<title>{esc(FIRST_NAME)} {esc(LAST_NAME)}</title><defs>{clip}</defs><style>{style}</style>'
            + "".join(body) + "</svg>")


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    svg = build()
    (OUT_DIR / "terminal.svg").write_text(svg, encoding="utf-8")
    print(f"terminal.svg: {len(svg.encode()) / 1024:.0f} KB")
