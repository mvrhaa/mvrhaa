from __future__ import annotations

import datetime as dt
import functools
import html
import math
import pathlib
import random
import re
import sys
from zoneinfo import ZoneInfo

FIRST_NAME = "Ruslan"
LAST_NAME = "Murha"
HANDLE = "mvrha"
BANNER = "MVRHAA"
TIMEZONE = "Europe/Warsaw"
ROOT = pathlib.Path(__file__).resolve().parent
OUT_DIR = ROOT / "assets"
README = ROOT / "README.md"

FONT = ("ui-monospace,'SF Mono',SFMono-Regular,Menlo,Consolas,"
        "'Liberation Mono','DejaVu Sans Mono',monospace")
COL = {
    "bg": "#0d1117", "bar": "#161b22", "sep": "#21262d", "border": "#30363d",
    "light": "#30363d", "title": "#7d8590", "text": "#c9d1d9", "dim": "#6e7681",
    "cmd": "#f0f6fc", "user": "#58a6ff", "host": "#8b949e", "path": "#c9d1d9",
    "sym": "#6e7681", "cursor": "#58a6ff", "live": "#58a6ff",
}
BANNER_COLORS = ["#f0f6fc", "#d1d9e0", "#b1bac4", "#8f99a4", "#6e7681"]
BANNER_SHADOW = "#1b2a3e"
SCLERA = ["#22262c", "#343a42", "#4b525b", "#686f79", "#8b929c"]
IRIS = ["#0a1a2e", "#11294a", "#1a3f6b", "#24598f", "#3474b3", "#5793d1", "#93bde8"]
SHINE, VEIN, LID_UP, LID_LO = "#f2f8ff", "#3e4651", "#8b949e", "#545b65"

EYE_COLS, EYE_ROWS = 64, 26
ECW, ECH, EFS = 5.05, 8.6, 8.4
EW, EH = EYE_COLS * ECW, EYE_ROWS * ECH
A, HU, HL = 150.0, 100.0, 82.0
X0, Y0 = EW / 2, EH / 2 + (HU - HL) / 2
R, IRIS_R, PUPIL = 168.0, 70.0, 0.40
TH_I = math.asin(IRIS_R / R)
SCLERA_RAMP = ".,:;~=+*"
IRIS_SOFT = ".:;'`"
IRIS_DENSE = "0OQ8B#%&@"


def _norm(v):
    m = math.sqrt(sum(x * x for x in v))
    return tuple(x / m for x in v)


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _smooth(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def _hash(*vals):
    h = 2166136261
    for v in vals:
        h = ((h ^ (int(v * 7919) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    h ^= h >> 15
    h = (h * 0x2C1B3C6D) & 0xFFFFFFFF
    h ^= h >> 12
    return h / 0xFFFFFFFF


def _lids(x, k):
    u = (x - X0) / A
    if abs(u) >= 1:
        return None
    b = 1 - u * u
    up = Y0 - HU * b ** 0.78 * (1 - 0.10 * u)
    lo = Y0 + HL * b ** 0.95 * (1 + 0.05 * u)
    meet = Y0 + 0.32 * HL * b ** 0.95
    return meet + (up - meet) * k, meet + (lo - meet) * k ** 0.55


def _radial_char(dx, dy):
    a = math.atan2(dy, dx) % math.pi
    return "-\\|/-"[int((a + math.pi / 8) // (math.pi / 4))]


def render_eye(gx: float, gy: float, k: float) -> dict:
    cells = {}
    g = _norm((gx, gy, 1.0))
    e1 = _norm(_cross((0.0, 1.0, 0.0), g))
    e2 = _cross(g, e1)
    pcx, pcy = X0 + R * g[0], Y0 + R * g[1]
    shine = [(pcx - 0.34 * IRIS_R, pcy - 0.40 * IRIS_R, 0.19 * IRIS_R, 0.15 * IRIS_R),
             (pcx + 0.40 * IRIS_R, pcy + 0.30 * IRIS_R, 0.08 * IRIS_R, 0.07 * IRIS_R)]
    for r in range(EYE_ROWS):
        py = (r + 0.5) * ECH
        for c in range(EYE_COLS):
            px = (c + 0.5) * ECW
            lid = _lids(px, k)
            if lid is None or not (lid[0] < py - ECH / 2 and py + ECH / 2 < lid[1]):
                continue
            up, lo = lid
            span = max(1e-6, lo - up)
            shade = (0.45 + 0.55 * _smooth(0.0, 0.42, (py - up) / span)) \
                * (0.80 + 0.20 * _smooth(0.0, 0.2, (lo - py) / span))
            X, Y = (px - X0) / R, (py - Y0) / R
            n = (X, Y, math.sqrt(max(0.0, 1 - X * X - Y * Y)))
            rr = math.acos(max(-1.0, min(1.0, _dot(n, g)))) / TH_I
            jit = _hash(r, c) - 0.5
            d = [((px - sx) / rx) ** 2 + ((py - sy) / ry) ** 2 for sx, sy, rx, ry in shine]
            if rr < 1.05 and (d[0] < 1 or d[1] < 1):
                cells[(r, c)] = ("@#%&"[int(_hash(c, r, 3) * 4) % 4] if d[0] < 0.55 else "*", "hl")
                continue
            if rr < PUPIL:
                continue
            if rr < 1.0:
                rad = (rr - PUPIL) / (1 - PUPIL)
                phi = math.atan2(_dot(n, e2), _dot(n, e1))
                fib = (0.5 + 0.30 * math.sin(phi * 17 + 1.8 * math.sin(phi * 5 + 0.4))
                       + 0.18 * math.sin(phi * 43 + 2.2 * math.sin(phi * 3 + rad * 4))
                       + 0.10 * math.sin(phi * 89 + rad * 11))
                v = 0.40 + 0.42 * fib
                v += 0.26 * math.exp(-((rad - 0.30) / 0.11) ** 2)
                v *= 1 - 0.60 * _smooth(0.76, 1.0, rad)
                v *= 0.55 + 0.45 * _smooth(0.0, 0.12, rad)
                v *= shade
                if d[0] < 2.4:
                    v += 0.16 * (2.4 - d[0]) / 2.4
                v = min(0.999, max(0.0, v + jit * 0.08))
                if v < 0.24:
                    ch = IRIS_SOFT[int(_hash(r, c, 5) * len(IRIS_SOFT))]
                elif v > 0.58:
                    ch = IRIS_DENSE[int(_hash(r, c, 6) * len(IRIS_DENSE))]
                else:
                    ch = _radial_char(px - pcx, py - pcy)
                cells[(r, c)] = (ch, f"i{int(v * len(IRIS))}")
                continue
            v = 0.74 * (0.30 + 0.70 * n[2] ** 0.65)
            if rr < 1.2:
                v *= 0.66 + 0.34 * _smooth(1.0, 1.2, rr)
            v = min(0.999, max(0.0, v * shade + jit * 0.05))
            u = abs(px - X0) / A
            if u > 0.6 and _hash(c, r, 7) < 0.05 * (u - 0.6) / 0.4:
                cells[(r, c)] = ("~", "vn")
                continue
            idx = int(v * (len(SCLERA_RAMP) - 1) + jit * 1.2)
            cells[(r, c)] = (SCLERA_RAMP[max(0, min(len(SCLERA_RAMP) - 1, idx))],
                             f"s{int(v * len(SCLERA))}")
    for key, val in _lid_cells(k).items():
        cells.setdefault(key, val)
    return cells


def _lid_cells(k: float) -> dict:
    closed = k < 0.06
    cells = {}
    for which, cls in ((0, "lu"), (1, "ll")):
        if closed and which == 1:
            continue
        rows = {}
        for c in range(EYE_COLS):
            x = (c + 0.5) * ECW
            lid = _lids(x, k)
            if lid is None:
                continue
            a, b = _lids(x - 0.5, k) or lid, _lids(x + 0.5, k) or lid
            s = (b[which] - a[which]) * ECW / ECH
            yv = lid[which] / ECH
            r, f = int(yv), yv - int(yv)
            if abs(s) > 0.75:
                ch = "/" if s < 0 else "\\"
            else:
                ch = "'" if f < 0.3 else "-" if f < 0.55 else "." if f < 0.8 else "_"
            cells.setdefault((r, c), (ch, cls))
            pr = rows.get(c - 1)
            rows[c] = r
            if pr is not None and abs(pr - r) > 1:
                outer = c - 1 if (c - 0.5) * ECW < X0 else c
                fill = "/" if pr > r else "\\"
                for rr in range(min(pr, r) + 1, max(pr, r)):
                    cells.setdefault((rr, outer), (fill, cls))
    return cells


def esc(s: str) -> str:
    return html.escape(s, quote=False)


def text_el(x, y, segs, cw, attrs=""):
    n = sum(len(t) for t, _ in segs)
    body = "".join(f'<tspan class="{c}">{esc(t)}</tspan>' if c else esc(t) for t, c in segs)
    return (f'<text x="{x:.1f}" y="{y:.1f}" textLength="{n * cw:.1f}" '
            f'lengthAdjust="spacingAndGlyphs"{(" " + attrs.strip()) if attrs else ""}>{body}</text>')


def eye_svg(cells, ox, oy):
    out = []
    for r in range(EYE_ROWS):
        cols = sorted(c for (rr, c) in cells if rr == r)
        if not cols:
            continue
        segs, cur, buf = [], None, ""
        for c in range(cols[0], cols[-1] + 1):
            ch, cls = cells.get((r, c), (" ", None))
            if ch != " " and cls != cur:
                if buf:
                    segs.append((buf, cur))
                buf, cur = "", cls
            buf += ch
        segs.append((buf, cur))
        out.append(text_el(ox + cols[0] * ECW, oy + r * ECH + ECH * 0.8, segs, ECW))
    return "".join(out)


def window(x, y, w, h, title):
    r = 10
    lights = "".join(f'<circle cx="{x + cx}" cy="{y + BAR / 2}" r="5.5" fill="{COL["light"]}"/>'
                     for cx in (18, 36, 54))
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{COL["bg"]}"/>'
            f'<path d="M{x + r} {y}h{w - 2 * r}a{r} {r} 0 0 1 {r} {r}v{BAR - r}h{-w}v{r - BAR}'
            f'a{r} {r} 0 0 1 {r} {-r}z" fill="{COL["bar"]}"/>'
            f'<path d="M{x} {y + BAR + 0.5}h{w}" stroke="{COL["sep"]}"/>' + lights
            + f'<text x="{x + w / 2}" y="{y + 19}" text-anchor="middle" class="wt">{esc(title)}</text>')


def window_border(x, y, w, h):
    return (f'<rect x="{x + 0.5}" y="{y + 0.5}" width="{w - 1}" height="{h - 1}" rx="9.5" '
            f'fill="none" stroke="{COL["border"]}"/>')


def keyframes(name, spans, total):
    merged = []
    for s, e in sorted(spans):
        if merged and s <= merged[-1][1] + 1e-9:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    pts = [(0.0, 0)]
    for s, e in merged:
        if s <= 1e-9:
            pts[0] = (0.0, 1)
        else:
            pts.append((s, 1))
        pts.append((min(e, total), 0))
    if pts[-1][0] < total - 1e-9:
        pts.append((total, pts[-1][1]))
    body = "".join(f"{100 * t / total:.4g}%{{opacity:{v}}}" for t, v in pts)
    return f"@keyframes {name}{{{body}}}"


def prompt(path="~"):
    return [(HANDLE, "cu"), ("@", "cs"), ("github", "ch"), (" ", None), (path, "cp"), (" % ", "cs")]


@functools.cache
def banner_rows():
    try:
        import pyfiglet
    except ImportError:
        print("pyfiglet is not installed, so the block-letter banner is left out "
              "(pip install pyfiglet)", file=sys.stderr)
        return []
    rows = pyfiglet.figlet_format(BANNER, font="ansi_shadow", width=200).split("\n")
    return [re.sub(r"[^█]", " ", row).rstrip() for row in rows if "█" in row]


def banner_svg(rows, x, y, cw, rh, t0, animated=True):
    parts = []
    for i, row in enumerate(rows):
        yy = y + i * rh
        main, shadow = [], []
        for m in re.finditer("█+", row):
            bx, bw = x + m.start() * cw, (m.end() - m.start()) * cw
            shadow.append(f'<rect x="{bx + 2:.1f}" y="{yy + 2:.1f}" width="{bw:.1f}" height="{rh:.1f}"/>')
            main.append(f'<rect x="{bx:.1f}" y="{yy:.1f}" width="{bw:.1f}" height="{rh:.1f}"/>')
        group = (f'<g class="on" style="animation-duration:{t0 + i * 0.04:.3f}s" '
                 if animated else "<g ")
        parts.append(group + 'shape-rendering="crispEdges">'
                     f'<g fill="{BANNER_SHADOW}">{"".join(shadow)}</g>'
                     f'<g fill="{BANNER_COLORS[i % len(BANNER_COLORS)]}">{"".join(main)}</g></g>')
    return "".join(parts)


def with_saccades(seq):
    out = []
    for t0, st in seq:
        if out and st[2] == 1.0 and out[-1][1][2] == 1.0:
            prev = out[-1][1]
            if math.hypot(st[0] - prev[0], st[1] - prev[1]) > 0.42:
                mx = round((st[0] + prev[0]) * 10) / 20
                my = round((st[1] + prev[1]) * 10) / 20
                out.append((t0, (mx, my, 1.0, st[3])))
                t0 += 0.04
        out.append((t0, st))
    return out


LEFT_W, RIGHT_W, MARGIN, GAP, BAR, PAD = 350, 484, 6, 14, 30, 14
TFS, TCW, TLH = 12.2, 7.35, 17.4
BANNER_CW, BANNER_ASPECT = 10.0, 1.93
LFS, LCW = 11, 6.6
EYE_TOP = BAR + 30
EYE_WIN_H = math.ceil(EYE_TOP + EH + 16 + PAD)


def build(wide: bool) -> tuple[str, int]:
    if wide:
        lx, ly, lw = MARGIN, MARGIN, LEFT_W
        rx, ry = MARGIN + LEFT_W + GAP, MARGIN
        gaze_scale = (1000.0, 650.0)
    else:
        lx, ly, lw = MARGIN, MARGIN, RIGHT_W
        rx, ry = MARGIN, MARGIN + EYE_WIN_H + GAP
        gaze_scale = (700.0, 1300.0)

    css = []

    tx, y = rx + PAD, ry + BAR + 10
    try:
        now = dt.datetime.now(ZoneInfo(TIMEZONE))
    except Exception:
        now = dt.datetime.now()
    term = [text_el(tx, y + TLH * 0.74, [(f"Last login: {now:%a %b %d %H:%M:%S} on ttys001", "cm")], TCW)]
    y += TLH

    banner = banner_rows()
    bcw = min(BANNER_CW, (RIGHT_W - 2 * PAD) / max([1] + [len(row) for row in banner]))
    brh = bcw * BANNER_ASPECT
    name = [(f"{FIRST_NAME} {LAST_NAME}", "cn"), ("  —  ", "cm"), ("hello, world", "cm")]
    session = [
        ("whoami", ([("banner", len(banner) * brh + 10)] if banner else []) + [(name, TLH)]),
    ]
    strip_output_parts = []
    command_y = y
    looks = []
    marks = {}
    t = 0.75
    for i, (cmd, outputs) in enumerate(session):
        if i:
            y += 7
        p = prompt()
        plen = sum(len(s) for s, _ in p)
        t_type = t + (0.55 if i == 0 else 0.35)
        typing = len(cmd) * 0.065
        t_enter = t_type + typing + 0.22
        cx, move = tx + plen * TCW, len(cmd) * TCW
        css.append(f"@keyframes ty{i}{{0%{{transform:translateX(0)}}"
                   f"{100 * t_type / (t_type + typing):.4g}%{{transform:translateX(0);"
                   f"animation-timing-function:steps({len(cmd)},end)}}"
                   f"100%{{transform:translateX({move:.1f}px)}}}}")
        term.append(
            f'<g class="on" style="animation-duration:{t:.2f}s">'
            + text_el(tx, y + TLH * 0.74, p + [(cmd, "cc")], TCW)
            + f'<g transform="translate({move:.1f},0)" style="animation:ty{i} {t_type + typing:.3f}s linear both">'
            + f'<rect x="{cx:.1f}" y="{y:.1f}" width="{move + TCW + 1:.1f}" height="{TLH:.1f}" fill="{COL["bg"]}"/>'
            + f'<g class="cw" style="animation-duration:{t_enter:.2f}s">'
              f'<rect x="{cx:.1f}" y="{y + 2:.1f}" width="{TCW:.1f}" height="{TLH - 3:.1f}" fill="{COL["cursor"]}"/></g>'
            + "</g></g>")
        looks.append((t, cx + move / 2, y + TLH / 2))
        y += TLH
        t_out = t_enter + 0.05
        block_top, width, delay = y, 0.0, t_out
        for segs, lh in outputs:
            if segs == "banner":
                term.append(banner_svg(banner, tx, y + 4, bcw, brh, delay))
                strip_output_parts.append(banner_svg(banner, tx, y + 4, bcw, brh, delay, animated=False))
                w = max(len(row) for row in banner) * bcw
                marks["banner"] = (tx + w / 2, y + lh / 2)
                delay += 0.04 * len(banner)
            else:
                w = sum(len(s) for s, _ in segs) * TCW
                if segs is name:
                    marks["name"] = (tx + w / 2, y + lh / 2)
                term.append(f'<g class="on" style="animation-duration:{delay:.3f}s">'
                            + text_el(tx, y + lh * 0.74, segs, TCW) + "</g>")
                strip_output_parts.append(text_el(tx, y + lh * 0.74, segs, TCW))
                delay += 0.035
            width = max(width, w)
            y += lh
        looks.append((t_out, tx + width / 2, (block_top + y) / 2))
        t = delay + 0.5
    y += 7
    p = prompt()
    plen = sum(len(s) for s, _ in p)
    term.append(f'<g class="on" style="animation-duration:{t:.2f}s">'
                + text_el(tx, y + TLH * 0.74, p, TCW)
                + f'<rect class="cur" x="{tx + plen * TCW:.1f}" y="{y + 2:.1f}" width="{TCW:.1f}" '
                  f'height="{TLH - 3:.1f}" fill="{COL["cursor"]}"/></g>')
    looks.append((t, tx + plen * TCW, y + TLH / 2))
    t_final = t
    term_h = math.ceil(y + TLH + PAD - ry)

    if wide:
        eye_h = term_h = max(EYE_WIN_H, term_h)
        W, H = MARGIN * 2 + LEFT_W + GAP + RIGHT_W, MARGIN * 2 + term_h
    else:
        eye_h = EYE_WIN_H
        W, H = MARGIN * 2 + RIGHT_W, MARGIN * 2 + eye_h + GAP + term_h

    ex, ey = lx + (lw - EW) / 2, ly + EYE_TOP
    ecx, ecy = ex + X0, ey + Y0
    left = [text_el(lx + PAD, ly + BAR + 24, prompt("~/eye") + [("./eye --ascii --watch", "cc")], LCW)]

    def gaze(px, py):
        gx, gy = (px - ecx) / gaze_scale[0], (py - ecy) / gaze_scale[1]
        m = math.hypot(gx, gy)
        if m > 0.55:
            gx, gy = gx * 0.55 / m, gy * 0.55 / m
        gy = min(0.32, max(-0.22, gy))
        return round(gx * 20) / 20, round(gy * 20) / 20

    def blink(t0, gx, gy, after):
        return [(t0, (gx, gy, 0.45, "blink")), (t0 + 0.04, (gx, gy, 0.12, "blink")),
                (t0 + 0.08, (gx, gy, 0.0, "blink")), (t0 + 0.17, (gx, gy, 0.12, "blink")),
                (t0 + 0.21, (gx, gy, 0.45, "blink")), (t0 + 0.25, (gx, gy, 1.0, after))]

    intro = [(0.0, (0, 0, 0.0, "waking up")), (0.35, (0, 0, 0.12, "waking up")),
             (0.42, (0, 0, 0.45, "waking up")), (0.5, (0, 0, 1.0, "watching you"))]
    for tl, px, py in looks:
        intro.append((tl, (*gaze(px, py), 1.0, "reading the terminal")))
    intro.append((t_final + 1.0, (0, 0, 1.0, "watching you")))
    intro += blink(t_final + 1.7, 0, 0, "watching you")
    t_intro = round(t_final + 2.6, 2)

    look_banner = gaze(*marks.get("banner", marks["name"]))
    look_name = gaze(*marks["name"])
    loop = [(0.0, (0, 0, 1.0, "watching you")),
            (1.8, (-0.45, 0.05, 1.0, "looking around")),
            (2.9, (-0.35, -0.2, 1.0, "looking around")),
            (3.7, (0, 0, 1.0, "watching you"))]
    loop += blink(4.3, 0, 0, "watching you")
    loop += [(5.6, (*look_banner, 1.0, "reading the terminal")),
             (6.8, (*look_name, 1.0, "reading the terminal")),
             (7.8, (0, 0, 1.0, "watching you")),
             (8.8, (-0.25, 0.3, 1.0, "looking around")),
             (9.7, (0, 0, 1.0, "watching you"))]
    loop += blink(10.3, 0, 0, "watching you") + blink(10.75, 0, 0, "watching you")
    loop += [(11.6, (0.3, -0.2, 1.0, "looking around")),
             (12.5, (0, 0, 1.0, "watching you"))]
    t_loop = 13.6

    frames, labels = {}, {}

    def spans(seq, total, which):
        seq = with_saccades(sorted(seq))
        for i, (t0, (gx, gy, k, label)) in enumerate(seq):
            t1 = seq[i + 1][0] if i + 1 < len(seq) else total
            frames.setdefault((gx, gy, k), {"i": [], "l": []})[which].append((t0, t1))
            labels.setdefault(label, {"i": [], "l": []})[which].append((t0, t1))

    spans(intro, t_intro, "i")
    spans(loop, t_loop, "l")
    phase = -round((t_loop - t_intro % t_loop) % t_loop, 3)

    eyes = []
    for n, ((gx, gy, k), sp) in enumerate(frames.items()):
        css.append(keyframes(f"i{n}", sp["i"], t_intro))
        css.append(keyframes(f"l{n}", sp["l"], t_loop))
        css.append(f".f{n}{{animation:l{n} {t_loop}s step-end {phase}s infinite,i{n} {t_intro}s step-end}}")
        start = " fs" if (gx, gy, k) == (0, 0, 1.0) else ""
        eyes.append(f'<g id="ef{n}" class="fr f{n}{start}"><g class="e">'
                    f'{eye_svg(render_eye(gx, gy, k), ex, ey)}</g></g>')
    status_y = ey + EH + 16
    status_x = lx + PAD + 9 * LCW
    status = [text_el(lx + PAD, status_y, [("●", "lv")], LCW),
              text_el(lx + PAD + 2 * LCW, status_y, [("live", "cm"), (" · ", "cs")], LCW)]
    for n, (label, sp) in enumerate(labels.items()):
        css.append(keyframes(f"si{n}", sp["i"], t_intro))
        css.append(keyframes(f"sl{n}", sp["l"], t_loop))
        css.append(f".lb{n}{{animation:sl{n} {t_loop}s step-end {phase}s infinite,si{n} {t_intro}s step-end}}")
        start = " fs" if label == "watching you" else ""
        status.append(f'<g class="fr lb{n}{start}">'
                      + text_el(status_x, status_y, [(label, "co")], LCW) + "</g>")

    frame_items = list(frames.items())
    frame_ids = {state: n for n, (state, _) in enumerate(frame_items)}
    frame_cells = {n: render_eye(*state) for n, (state, _) in enumerate(frame_items)}

    def active_frame(at):
        if at < t_intro:
            local, seq = at, with_saccades(sorted(intro))
        else:
            local = (at - t_intro + phase) % t_loop
            seq = with_saccades(sorted(loop))
        state = seq[0][1]
        for event_time, event_state in seq:
            if event_time > local:
                break
            state = event_state
        return frame_ids[tuple(state[:3])]

    def active_frames(start_at, end_at):
        samples = max(1, math.ceil((end_at - start_at) / 0.01))
        return sorted({active_frame(min(end_at - 1e-6, start_at + i * 0.01))
                       for i in range(samples + 1)})

    def crop_cells(cells, rect):
        row, col, height, width = rect
        return {(r, c): value for (r, c), value in cells.items()
                if row <= r < row + height and col <= c < col + width}

    def brighten(cells):
        brighter = {}
        for key, (char, cls) in cells.items():
            if cls and cls[0] in "si" and cls[1:].isdigit():
                colors = SCLERA if cls[0] == "s" else IRIS
                brighter[key] = (char, f"{cls[0]}{min(int(cls[1:]) + 1, len(colors) - 1)}")
            else:
                brighter[key] = (char, cls)
        return brighter

    def glitch_cells(cells, rect):
        row, col, height, width = rect
        shifted, offsets = {}, {}
        for (r, c), value in crop_cells(cells, rect).items():
            if r not in offsets:
                offsets[r] = rng.randint(-3, 3)
            shifted[(r, c + offsets[r])] = value
        count = min(len(shifted), int(4 + width / 3))
        for key in rng.sample(list(shifted), count):
            shifted[key] = (rng.choice(glitch_chars), "gc")
        return shifted

    rng = random.Random(12)
    glitch_chars = "▓▒░█▚▞#@%$&?/\\|"
    straight = render_eye(0, 0, 1.0)
    spawn_offsets = [0.35]
    for gap in (0.6, 0.9, 0.55, 0.8, 0.5, 0.95, 0.7):
        spawn_offsets.append(spawn_offsets[-1] + gap)
    spawn_times = [t_out + offset for offset in spawn_offsets]
    loads = ("1.12", "2.40", "3.87", "5.06", "6.71", "8.33", "9.98")
    mini_specs = []
    for index, spawned_at in enumerate(spawn_times):
        for attempt in range(10000):
            width, height = rng.randint(9, 16), rng.randint(4, 7)
            col = rng.randint(1, EYE_COLS - width - 1)
            row = rng.randint(2, EYE_ROWS - height - 1)
            rect = (row, col, height, width)
            occupied = len(crop_cells(straight, rect))
            if occupied >= 0.8 * width * height:
                break
        else:
            raise RuntimeError("Could not find a sufficiently dense mini-terminal placement")
        mini_specs.append((index, spawned_at, rect, loads[min(index, len(loads) - 1)]))

    overload_at = spawn_times[6] + 0.75
    kill_at = overload_at + 6 * 0.08
    watching_at = kill_at + 0.9
    scene_end = watching_at + 0.2

    def visible_class(name, span):
        css.append(keyframes(f"v{name}", [span], scene_end))
        css.append(f".{name}{{animation:v{name} {scene_end:.3f}s step-end both}}")
        return name

    mini_markup, extra_defs = [], []
    mini_tints = "".join(
        f".mini .s{i}{{fill:{SCLERA[min(i + 1, len(SCLERA) - 1)]}}}"
        f".mini .i{i}{{fill:{IRIS[min(i + 1, len(IRIS) - 1)]}}}"
        for i in range(len(SCLERA))
    )
    for index, spawned_at, rect, _load in mini_specs:
        row, col, height, width = rect
        x, y0 = ex + col * ECW, ey + row * ECH
        box_x, box_y = x - 2, y0 - 11
        box_w, box_h = width * ECW + 4, height * ECH + 13
        content_clip = f"mc{index}"
        extra_defs.append(
            f'<clipPath id="{content_clip}"><rect x="{x:.2f}" y="{y0:.2f}" '
            f'width="{width * ECW:.2f}" height="{height * ECH:.2f}"/></clipPath>')
        live_until = kill_at
        window_class = visible_class(f"mw{index}", (spawned_at, live_until))
        glitch_class = visible_class(f"mg{index}", (spawned_at, spawned_at + 0.14))
        snapshot_class = visible_class(f"ms{index}", (spawned_at + 0.14, spawned_at + 0.5))
        sync_class = visible_class(f"my{index}", (spawned_at + 0.5, live_until))
        title_class = visible_class(f"mt{index}", (spawned_at, spawned_at + 0.5))
        sync_title_class = visible_class(f"mu{index}", (spawned_at + 0.5, live_until))
        initial_cells = brighten(glitch_cells(frame_cells[active_frame(spawned_at)], rect))
        snapshot_cells = brighten(crop_cells(frame_cells[active_frame(spawned_at)], rect))
        overload_cells = brighten(glitch_cells(frame_cells[active_frame(overload_at)], rect))
        sync_frames = active_frames(spawned_at + 0.5, live_until)
        mini_markup.append(
            f'<g class="mini {window_class}">'
            f'<rect x="{box_x:.2f}" y="{box_y:.2f}" width="{box_w:.2f}" height="{box_h:.2f}" '
            f'rx="2" fill="#0a1220" stroke="#58a6ff" stroke-width="0.8"/>'
            f'<path d="M{box_x:.2f} {y0 - 1.5:.2f}h{box_w:.2f}" stroke="#1f3a5f"/>'
            f'<g class="{title_class}"><text x="{box_x + 3:.2f}" y="{y0 - 4:.2f}" '
            f'font-size="7" fill="#58a6ff">pts/{index + 1}</text></g>'
            f'<g class="{sync_title_class}"><text x="{box_x + 3:.2f}" y="{y0 - 4:.2f}" '
            f'font-size="7" fill="#58a6ff">pts/{index + 1} · sync</text></g>'
            f'<g clip-path="url(#{content_clip})">'
            f'<g class="{glitch_class}"><g class="e">{eye_svg(initial_cells, ex, ey)}</g></g>'
            f'<g class="{snapshot_class}"><g class="e">{eye_svg(snapshot_cells, ex, ey)}</g></g>'
            f'<g class="{sync_class}">'
            + "".join(f'<g class="fr f{n}"><g class="e">'
                      f'{eye_svg(brighten(crop_cells(cells, rect)), ex, ey)}</g></g>'
                      for n, cells in frame_cells.items() if n in sync_frames)
            + f'</g><g class="{visible_class(f"mo{index}", (overload_at, kill_at))}">'
            f'<g class="e">{eye_svg(overload_cells, ex, ey)}</g></g></g></g>')

    status_events = []
    for index, spawned_at, _rect, load in mini_specs:
        next_time = mini_specs[index + 1][1] if index + 1 < len(mini_specs) else overload_at
        status_events.append((spawned_at, next_time, f"pts/{index + 1} spawned · load {load}"))
    status_events.extend(((overload_at, kill_at, "overload · load 12.40"),
                          (kill_at, watching_at, "killall · load 0.41"),
                          (watching_at, scene_end, "watching you")))
    status_overlay = []
    for index, (start_at, end_at, label) in enumerate(status_events):
        vis = visible_class(f"st{index}", (start_at, end_at))
        status_overlay.append(
            f'<g class="{vis}"><rect x="{status_x - 2:.2f}" y="{status_y - LFS + 1:.2f}" '
            f'width="{lw - PAD - (status_x - lx):.2f}" height="{LFS + 2}" fill="{COL["bg"]}"/>'
            f'{text_el(status_x, status_y, [(label, "co")], LCW)}</g>')

    command_text = text_el(tx, command_y + TLH * 0.74, p + [("whoami", "cc")], TCW)
    left_command = left[0]
    left_strip = (f'<g id="eyeStripContent"><g class="e">'
                  + "".join(f'<use href="#ef{n}" class="fr f{n}"/>' for n in range(len(frame_items)))
                  + f'</g>{left_command}</g>')
    right_strip = (f'<g id="shellStripContent">{command_text}'
                   f'{"".join(strip_output_parts)}</g>')
    extra_defs.extend((left_strip, right_strip))

    glitch_chars_array = tuple(glitch_chars)
    glitch_colors = ("#58a6ff", "#7ee7f5", "#f0f6fc", "#1f6feb", "#ff2bd6", "#ff3b5c")
    glitch_events = []
    for index, spawned_at in enumerate(spawn_times):
        intensity = 1 + 0.55 * index
        for subframe in range(3):
            start_at = spawned_at + subframe * 0.07
            glitch_events.append((start_at, start_at + 0.07, intensity))
    for subframe in range(6):
        start_at = overload_at + subframe * 0.08
        glitch_events.append((start_at, start_at + 0.08, 5.5))

    eye_ghosts, nickname_ghosts, red_eyes, glitch_top = [], [], [], []
    shake_events = []
    strip_clip_index = 0
    for event_index, (start_at, end_at, intensity) in enumerate(glitch_events):
        vis = visible_class(f"gx{event_index}", (start_at, end_at))
        eye_shift = 2 + 0.9 * intensity
        eye_ghosts.append(
            f'<g class="{vis}">'
            + "".join(f'<use href="#ef{n}" class="fr f{n}" filter="url(#tC)" '
                      f'transform="translate({-eye_shift:.2f} 0)" opacity="0.8"/>'
                      f'<use href="#ef{n}" class="fr f{n}" filter="url(#tM)" '
                      f'transform="translate({eye_shift:.2f} 0)" opacity="0.85"/>'
                      for n in range(len(frame_items))) + "</g>")
        nick_shift = 3 + 1.4 * intensity
        nick_cyan = text_el(tx, command_y + TLH * 0.74, [(HANDLE, None)], TCW,
                            'fill="#00e5ff"')
        nick_magenta = text_el(tx, command_y + TLH * 0.74, [(HANDLE, None)], TCW,
                               'fill="#ff2bd6"')
        nickname_ghosts.append(
            f'<g class="{vis}"><g transform="translate({-nick_shift:.2f} 0)" '
            f'opacity="0.85">{nick_cyan}</g><g transform="translate({nick_shift:.2f} 0)" '
            f'opacity="0.9">{nick_magenta}</g></g>')
        red_eyes.append(
            f'<g class="{vis}">'
            + "".join(f'<use href="#ef{n}" class="fr f{n}" filter="url(#tR)"/>'
                      for n in range(len(frame_items))) + "</g>")

        overlays = []
        for window_index, (win_x, win_y, win_w, win_h) in enumerate(
                ((lx, ly, lw, eye_h), (rx, ry, RIGHT_W, term_h))):
            direction = 1 if window_index == 0 else -1
            for _ in range(int(1 + intensity)):
                strip_h = rng.uniform(4, 8 + 2.2 * intensity)
                min_y = win_y + BAR + 1
                max_y = max(min_y, win_y + win_h - strip_h - 1)
                strip_y = rng.uniform(min_y, max_y)
                clip_id = f"gc{strip_clip_index}"
                strip_clip_index += 1
                extra_defs.append(
                    f'<clipPath id="{clip_id}"><rect x="{win_x}" y="{strip_y:.2f}" '
                    f'width="{win_w}" height="{strip_h:.2f}"/></clipPath>')
                magnitude = rng.uniform(3, 4 + 3.5 * intensity)
                dx = direction * magnitude
                use_id = "eyeStripContent" if window_index == 0 else "shellStripContent"
                overlays.append(
                    f'<rect x="{win_x}" y="{strip_y:.2f}" width="{win_w}" height="{strip_h:.2f}" '
                    f'fill="#0d1117"/><g clip-path="url(#{clip_id})">'
                    f'<use href="#{use_id}" transform="translate({dx:.2f} 0)"/></g>')

            for _ in range(1 + int(intensity / 2)):
                gy = rng.uniform(win_y + BAR + 2, win_y + win_h - 2)
                color = rng.choice(("#00e5ff", "#ff2bd6"))
                overlays.append(f'<rect x="{win_x}" y="{gy:.2f}" width="{win_w}" height="1.2" '
                                f'fill="{color}" opacity="0.65"/>')
        for _ in range(int(2 + intensity)):
            win_x, win_y, win_w, win_h = rng.choice(
                ((lx, ly, lw, eye_h), (rx, ry, RIGHT_W, term_h)))
            text = "".join(rng.choice(glitch_chars_array) for _ in range(rng.randint(3, 10)))
            gx = rng.uniform(win_x + 2, win_x + win_w - 48)
            gy = rng.uniform(win_y + BAR + 10, win_y + win_h - 4)
            color = rng.choice(glitch_colors)
            size = rng.choice((8.4, 12.2))
            overlays.append(f'<text x="{gx:.2f}" y="{gy:.2f}" font-size="{size}" '
                            f'fill="{color}">{esc(text)}</text>')
        glitch_top.append(f'<g class="{vis}">{"".join(overlays)}</g>')
        shake_events.append((start_at, end_at, intensity,
                             rng.uniform(-(0.6 + 0.5 * intensity), 0.6 + 0.5 * intensity),
                             rng.uniform(-0.4 * intensity, 0.4 * intensity)))

    shake_points = []
    shake_times = sorted({0.0, scene_end} |
                         {t for start_at, end_at, *_ in shake_events for t in (start_at, end_at)})
    for time in shake_times:
        active = [event for event in shake_events if event[0] <= time < event[1]]
        if active:
            _, _, _, dx, dy = max(active, key=lambda event: event[2])
        else:
            dx, dy = 0.0, 0.0
        shake_points.append(f"{100 * time / scene_end:.4g}%"
                            f"{{transform:translate({dx:.2f}px,{dy:.2f}px)}}")
    css.append(f"@keyframes shake{{{''.join(shake_points)}}}")

    body = [
        '<g class="scene">',
        window(lx, ly, lw, eye_h, f"eye — ascii — {EYE_COLS}×{EYE_ROWS}"),
        window(rx, ry, RIGHT_W, term_h, f"{HANDLE}@github: ~ — zsh — 80×24"),
        f'<g class="l">{"".join(left)}</g>',
        "".join(eye_ghosts),
        "".join(nickname_ghosts),
        f'<g class="t" clip-path="url(#clipT)">{"".join(term)}</g>',
        f'<g class="e">{"".join(eyes)}</g>',
        "".join(red_eyes),
        "".join(mini_markup),
        f'<g class="l">{"".join(status)}{"".join(status_overlay)}</g>',
        window_border(rx, ry, RIGHT_W, term_h),
        window_border(lx, ly, lw, eye_h),
        "".join(glitch_top),
        '</g>',
    ]

    classes = {f"s{i}": c for i, c in enumerate(SCLERA)} | {f"i{i}": c for i, c in enumerate(IRIS)} \
        | {"hl": SHINE, "vn": VEIN, "lu": LID_UP, "ll": LID_LO, "cu": COL["user"], "cs": COL["sym"],
           "ch": COL["host"], "cp": COL["path"], "cc": COL["cmd"], "cm": COL["dim"], "co": COL["text"],
           "cn": COL["cmd"], "lv": COL["live"]}
    style = (f"text{{font-family:{FONT};white-space:pre;fill:{COL['text']}}}"
             f".e text{{font-size:{EFS}px}}.t text{{font-size:{TFS}px}}.l text{{font-size:{LFS}px}}"
             ".mini text{font-weight:700}"
             f".wt{{font-size:12px!important;fill:{COL['title']}!important;white-space:normal}}"
             ".cn{font-weight:700}"
             + "".join(f".{k}{{fill:{v}}}" for k, v in classes.items())
             + mini_tints
             + ".gc{fill:#7ee7f5}"
             + ".fr{opacity:0}.fs{opacity:1}"
             ".on{animation-name:on;animation-timing-function:step-end;animation-fill-mode:both}"
             "@keyframes on{from{opacity:0}to{opacity:1}}"
             ".cw{opacity:0;animation-name:cw;animation-timing-function:step-end;animation-fill-mode:both}"
             "@keyframes cw{from{opacity:1}to{opacity:0}}"
             ".cur,.lv{animation:bl 1.1s step-end infinite}@keyframes bl{0%{opacity:1}50%{opacity:0}}"
             f".scene{{animation:shake {scene_end:.3f}s step-end both}}"
             + "".join(css))
    clip = (f'<clipPath id="clipT"><rect x="{rx}" y="{ry + BAR + 1}" width="{RIGHT_W}" '
            f'height="{term_h - BAR - 1}" rx="10"/></clipPath>')
    filters = (
        '<filter id="tC" x="-5%" y="-5%" width="110%" height="110%" '
        'color-interpolation-filters="sRGB"><feColorMatrix type="matrix" values="'
        '0 0 0 0 0  0 0 0 0 0.9  0 0 0 0 1  .5 .5 .5 0 -.12"/></filter>'
        '<filter id="tM" x="-5%" y="-5%" width="110%" height="110%" '
        'color-interpolation-filters="sRGB"><feColorMatrix type="matrix" values="'
        '0 0 0 0 1  0 0 0 0 0.17  0 0 0 0 0.84  .5 .5 .5 0 -.12"/></filter>'
        '<filter id="tR" color-interpolation-filters="sRGB"><feColorMatrix type="matrix" values="'
        '.62 .62 .62 0 .08  .06 .06 .06 0 0  .12 .12 .12 0 .02  0 0 0 1 0"/></filter>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
            f'xml:space="preserve" role="img" aria-label="{html.escape(alt_text())}">'
            f'<title>{esc(FIRST_NAME)} {esc(LAST_NAME)}</title>'
            f'<defs>{clip}{filters}{"".join(extra_defs)}</defs><style>{style}</style>'
            + "".join(body) + "</svg>"), len(frames)


def alt_text() -> str:
    return (f"Terminal session: {FIRST_NAME} {LAST_NAME} ({HANDLE}). "
            "An ASCII eye in the next window watches it being typed.")


def update_readme() -> None:
    if not README.exists():
        return
    text = README.read_text(encoding="utf-8")
    new, n = re.subn(r'(<img src="\./assets/terminal\.svg"[^>]*?\salt=")[^"]*(")',
                     lambda m: m.group(1) + html.escape(alt_text()) + m.group(2), text)
    if n == 0:
        print('README.md: no <img src="./assets/terminal.svg" ... alt="..."> found, left as is',
              file=sys.stderr)
    elif new != text:
        README.write_text(new, encoding="utf-8")
        print("README.md: image description updated")


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for file, wide in (("terminal.svg", True), ("terminal-mobile.svg", False)):
        svg, n_frames = build(wide)
        (OUT_DIR / file).write_text(svg, encoding="utf-8")
        print(f"{file}: {len(svg.encode()) / 1024:.0f} KB, {n_frames} eye frames")
    update_readme()
