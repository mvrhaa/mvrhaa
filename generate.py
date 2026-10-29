from __future__ import annotations

import html
import pathlib

FIRST_NAME = "Ruslan"
LAST_NAME = "Murha"
HANDLE = "mvrha"
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


LEFT_W, RIGHT_W, WIN_H, MARGIN, GAP, BAR, PAD = 350, 484, 330, 6, 14, 30, 14


def build() -> str:
    W, H = MARGIN * 2 + LEFT_W + GAP + RIGHT_W, MARGIN * 2 + WIN_H
    lx, ly = MARGIN, MARGIN
    rx, ry = MARGIN + LEFT_W + GAP, MARGIN

    body = [
        window(rx, ry, RIGHT_W, WIN_H, f"{HANDLE}@github: ~ — zsh — 80×24"),
        window_border(rx, ry, RIGHT_W, WIN_H),
        window(lx, ly, LEFT_W, WIN_H, "eye — ascii"),
        window_border(lx, ly, LEFT_W, WIN_H),
    ]

    style = (f"text{{font-family:{FONT};white-space:pre;fill:{COL['text']}}}"
             f".wt{{font-size:12px!important;fill:{COL['title']}!important;white-space:normal}}")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
            f'xml:space="preserve" role="img" aria-label="{esc(FIRST_NAME)} {esc(LAST_NAME)} — terminal">'
            f'<title>{esc(FIRST_NAME)} {esc(LAST_NAME)}</title><style>{style}</style>'
            + "".join(body) + "</svg>")


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    svg = build()
    (OUT_DIR / "terminal.svg").write_text(svg, encoding="utf-8")
    print(f"terminal.svg: {len(svg.encode()) / 1024:.0f} KB")
