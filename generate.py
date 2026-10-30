from __future__ import annotations

import functools
import html
import math
import pathlib
import random
import re
import sys

FIRST_NAME = "Ruslan"
LAST_NAME = "Murha"
HANDLE = "mvrha"
BANNER = "MVRHAA"
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


def num(v, digits=3):
    s = f"{v + 0.0:.{digits}f}".rstrip("0").rstrip(".")
    return s.replace("0.", ".", 1) if s.lstrip("-").startswith("0.") else s


def text_el(x, y, segs, cw, attrs=""):
    n = sum(len(t) for t, _ in segs)
    base = None
    if segs and all(c for _, c in segs):
        # the most frequent class moves up to <text>, so its runs need no <tspan>
        runs = [c for _, c in segs]
        base = max(dict.fromkeys(runs), key=runs.count)
        attrs = f'class="{base}" {attrs}'
    body = "".join(f'<tspan class="{c}">{esc(t)}</tspan>' if c and c != base else esc(t) for t, c in segs)
    return (f'<text x="{num(x, 1)}" y="{num(y, 1)}" textLength="{num(n * cw, 1)}" '
            f'lengthAdjust="spacingAndGlyphs"{(" " + attrs.strip()) if attrs else ""}>{body}</text>')


def eye_svg(cells, ox, oy, rows=range(EYE_ROWS)):
    out = []
    for r in rows:
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


def at(x, body):
    return f'<g transform="translate({x})">{body}</g>' if x else body


def steps(spans, idle, origin=0.0):
    out, end = [(0.0, idle)], None
    for start, stop, value in spans:
        if end is not None and start > end + 1e-9:
            out.append((end - origin, idle))
        out.append((start - origin, value))
        end = stop
    return out + ([(end - origin, idle)] if end is not None else [])


def _rgb(color):
    return [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]


def _hex(*vals):
    return "#" + "".join(f"{round(min(1.0, max(0.0, v)) * 255):02x}" for v in vals)


def red_tint(color):
    lum = sum(_rgb(color))
    return _hex(0.62 * lum + 0.08, 0.06 * lum, 0.12 * lum + 0.02)


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


def banner_svg(rows, x, y, cw, rh, t0, animated=True, row_offset=0):
    parts = []
    for i, row in enumerate(rows):
        row_index = row_offset + i
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
                     f'<g fill="{BANNER_COLORS[row_index % len(BANNER_COLORS)]}">{"".join(main)}</g></g>')
    return "".join(parts)


def with_tweens(seq):
    # a look slides through eased in-between gazes (on the 0.05 grid, so the way back reuses them)
    out = []
    for t0, st in seq:
        if out and st[2] == 1.0 and out[-1][1][2] == 1.0:
            px, py = out[-1][1][:2]
            count = min(3, round(math.hypot(st[0] - px, st[1] - py) / 0.15))
            for i in range(1, count + 1):
                e = _smooth(0.0, 1.0, i / (count + 1))
                mid = (round((px + (st[0] - px) * e) * 20) / 20, round((py + (st[1] - py) * e) * 20) / 20)
                if mid not in (out[-1][1][:2], st[:2]):
                    out.append((t0, (*mid, 1.0, st[3])))
                    t0 += 0.035
        out.append((t0, st))
    return out


LEFT_W, RIGHT_W, MARGIN, GAP, BAR, PAD = 350, 484, 6, 14, 30, 14
TFS, TCW, TLH = 12.2, 7.35, 17.4
BANNER_CW, BANNER_ASPECT = 10.0, 1.93
LFS, LCW = 11, 6.6
EYE_TOP = BAR + 30
# sprite pitch: a sprite keeps its other slots this far off-canvas, one transform step brings a slot in
OFF = 1000
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
    term = []

    banner = banner_rows()
    bcw = min(BANNER_CW, (RIGHT_W - 2 * PAD) / max([1] + [len(row) for row in banner]))
    brh = bcw * BANNER_ASPECT
    name = [(f"{FIRST_NAME} {LAST_NAME}", "cn"), ("  —  ", "cm"), ("hello, world", "cm")]
    session = [
        ("cat me", ([("banner", len(banner) * brh + 10)] if banner else []) + [(name, TLH)]),
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
                strip_output_parts.append(("banner", y + 4, brh, None))
                w = max(len(row) for row in banner) * bcw
                marks["banner"] = (tx + w / 2, y + lh / 2)
                delay += 0.04 * len(banner)
            else:
                w = sum(len(s) for s, _ in segs) * TCW
                if segs is name:
                    marks["name"] = (tx + w / 2, y + lh / 2)
                term.append(f'<g class="on" style="animation-duration:{delay:.3f}s">'
                            + text_el(tx, y + lh * 0.74, segs, TCW) + "</g>")
                strip_output_parts.append(("text", y, lh, segs))
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

    lids = (0.7, 0.4, 0.15, 0.0)

    def blink(t0, gx, gy, after):
        closing = [(t0 + i * 0.03, (gx, gy, k, "blink")) for i, k in enumerate(lids)]
        opening = [(t0 + 0.16 + i * 0.03, (gx, gy, k, "blink")) for i, k in enumerate(lids[-2::-1])]
        return closing + opening + [(t0 + 0.25, (gx, gy, 1.0, after))]

    intro = [(0.0, (0, 0, 0.0, "waking up"))]
    intro += [(0.35 + i * 0.045, (0, 0, k, "waking up")) for i, k in enumerate(lids[-2::-1])]
    intro.append((0.5, (0, 0, 1.0, "watching you")))
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

    seq_i, seq_l = with_tweens(sorted(intro)), with_tweens(sorted(loop))
    order = list(dict.fromkeys(tuple(state[:3]) for _, state in seq_i + seq_l))
    label_order = list(dict.fromkeys(state[3] for _, state in seq_i + seq_l))
    frame_ids = {state: n for n, state in enumerate(order)}
    frame_cells = {n: render_eye(*state) for n, state in enumerate(order)}
    keyframe_names = {}

    def animation(changes, duration, delay=0.0, infinite=False, fill=""):
        body = "".join(f"{k}{{{v}}}" for k, v in
                       {f"{100 * t / duration:.4g}%": v for t, v in changes}.items())
        name = keyframe_names.setdefault(body, f"k{len(keyframe_names)}")
        rule = f"animation:{name} {num(duration)}s step-end" + (f" {num(delay)}s" if delay else "")
        rule += (" infinite" if infinite else "") + (f" {fill}" if fill else "")
        # --d repeats the delay so a capture can freeze any moment with calc(var(--d) - T)
        return rule + (f";--d:{num(delay)}s" if delay else "")

    def shift_to(x):
        return f"transform:translate({num(-x)}px)" if x else "transform:none"

    # three eye loops per idle glitch, so every repeat meets the eye in the same pose
    idle_period = 3 * t_loop

    def timing(changes, start, stop, period):
        return animation(changes, period, start, True) if period else animation(changes, stop - start, start)

    def track(spans, idle, attrs, inner, period=None):
        start, stop = spans[0][0], spans[-1][1]
        return f'<g{attrs} style="{timing(steps(spans, idle, start), start, stop, period)}">{inner}</g>'

    def layer(spans, inner, shifts=None, period=None):
        # opacity, not visibility or display: it is not inherited, so flipping it never restyles the layer,
        # and a hidden layer is replayed from the paint cache instead of being repainted
        values = ["opacity:1" + (f";{shift_to(x)}" if x else "") for x in shifts or [0] * len(spans)]
        return track([(a, b, v) for (a, b), v in zip(spans, values)], "opacity:0", ' class="h"', inner, period)

    def sprite(slots, spans, period=None):
        # small sprites only: moving a group costs in proportion to everything inside it
        keys = list(slots)
        moves = sorted((a, b, shift_to(OFF * (i + 1))) for i, key in enumerate(keys) for a, b in spans[key])
        start, stop = moves[0][0], moves[-1][1]
        return (f'<g style="{timing(steps(moves, "transform:none", start), start, stop, period)}">'
                + "".join(at(OFF * (i + 1), slots[key]) for i, key in enumerate(keys)) + "</g>")

    def looped(pos, key, inner):
        intro_steps = [(t0, shift_to(pos[key(state)])) for t0, state in seq_i]
        loop_steps = [(t0, shift_to(pos[key(state)])) for t0, state in seq_l]
        return (f'<g style="{animation(intro_steps, t_intro)}">'
                f'<g style="{animation(loop_steps, t_loop, t_intro, True)}">{inner}</g></g>')

    def frame_spans(seq, total):
        spans = {}
        for i, (t0, state) in enumerate(seq):
            t1 = seq[i + 1][0] if i + 1 < len(seq) else total
            spans.setdefault(frame_ids[tuple(state[:3])], []).append((t0, t1, "opacity:1"))
        return spans

    label_pos = {k: OFF * i for i, k in enumerate(
        ["watching you"] + [k for k in label_order if k != "watching you"])}

    def shown_frame(at):
        local, seq = (at, seq_i) if at < t_intro else ((at - t_intro) % t_loop, seq_l)
        state = seq[0][1]
        for event_time, event_state in seq:
            if event_time > local:
                break
            state = event_state
        return frame_ids[tuple(state[:3])]

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

    loops_needed = math.ceil((scene_end + idle_period - t_intro) / t_loop) + 1
    cuts = sorted({t for t, _ in seq_i} | {t_intro + k * t_loop + t for k in range(loops_needed) for t, _ in seq_l})

    def segments(start, stop):
        points = [start] + [t for t in cuts if start < t < stop] + [stop]
        out = []
        for a, b in zip(points, points[1:]):
            n = shown_frame((a + b) / 2)
            if out and out[-1][0] == n:
                out[-1][2] = b
            else:
                out.append([n, a, b])
        return out

    extra_defs, minis = [], []
    for index, spawned_at, rect, _load in mini_specs:
        row, col, height, width = rect
        x, y0 = ex + col * ECW, ey + row * ECH
        box_x, box_y = x - 2, y0 - 11
        box_w, box_h = width * ECW + 4, height * ECH + 13
        extra_defs.append(
            f'<clipPath id="mc{index}"><rect x="{x:.2f}" y="{y0:.2f}" '
            f'width="{width * ECW:.2f}" height="{height * ECH:.2f}"/></clipPath>')
        box = (f'<rect x="{box_x:.2f}" y="{box_y:.2f}" width="{box_w:.2f}" height="{box_h:.2f}" '
               f'rx="2" fill="#0a1220" stroke="#58a6ff" stroke-width="0.8"/>'
               f'<path d="M{box_x:.2f} {y0 - 1.5:.2f}h{box_w:.2f}" stroke="#1f3a5f"/>')
        titles = [f'<text x="{box_x + 3:.2f}" y="{y0 - 4:.2f}" font-size="7" fill="#58a6ff">'
                  f'pts/{index + 1}{suffix}</text>' for suffix in ("", " · sync")]
        minis.append((spawned_at, rect, f"mc{index}", box, titles))

    def mini_cells(spawned_at, rect, offset):
        spawn_frame = frame_cells[shown_frame(spawned_at + offset)]
        return (brighten(glitch_cells(spawn_frame, rect)), brighten(crop_cells(spawn_frame, rect)),
                brighten(glitch_cells(frame_cells[shown_frame(overload_at + offset)], rect)))

    def mini_window(spec, cells, offset, period=None):
        spawned_at, rect, content_clip, box, titles = spec
        glitched, snapshot, overloaded = cells
        s, ov, kill = spawned_at + offset, overload_at + offset, kill_at + offset
        layers = {"g": eye_svg(glitched, ex, ey), "s": eye_svg(snapshot, ex, ey)}

        def mini_slot(stage, overload_now):
            if stage in ("g", "s"):
                title, rows = titles[0], layers[stage]
            else:
                title, rows = titles[1], eye_svg(brighten(crop_cells(frame_cells[stage], rect)), ex, ey)
            if overload_now:
                rows += eye_svg(overloaded, ex, ey)
            return title + f'<g clip-path="url(#{content_clip})"><g class="e">{rows}</g></g>'

        points = sorted(p for p in {s + 0.14, s + 0.5, ov, *cuts} if s < p < kill)
        slots, spans = {}, {}
        for a, b in zip([s] + points, points + [kill]):
            mid = (a + b) / 2
            stage = "g" if mid < s + 0.14 else "s" if mid < s + 0.5 else shown_frame(mid)
            key = (stage, mid > ov)
            slots.setdefault(key, None)
            spans.setdefault(key, []).append((a, b))
        content = sprite({key: mini_slot(*key) for key in slots}, spans, period)
        return track([(s, kill, "opacity:1")], "opacity:0", ' class="h mini" font-weight="700"',
                     box + content, period)

    mini_markup = [mini_window(spec, mini_cells(spec[0], spec[1], 0), 0) for spec in minis]

    status_y = ey + EH + 16
    status_x = lx + PAD + 9 * LCW
    status = [text_el(lx + PAD, status_y, [("●", "lv")], LCW),
              text_el(lx + PAD + 2 * LCW, status_y, [("live", "cm"), (" · ", "cs")], LCW),
              looped(label_pos, lambda state: state[3],
                     "".join(at(label_pos[label], text_el(status_x, status_y, [(label, "co")], LCW))
                             for label in label_order))]

    status_events = []
    for index, spawned_at, _rect, load in mini_specs:
        next_time = mini_specs[index + 1][1] if index + 1 < len(mini_specs) else overload_at
        status_events.append((spawned_at, next_time, f"pts/{index + 1} spawned · load {load}"))
    status_events.extend(((overload_at, kill_at, "overload · load 12.40"),
                          (kill_at, watching_at, "killall · load 0.41"),
                          (watching_at, scene_end, "watching you")))
    status_slots = "".join(
        at(OFF * (k + 1),
           f'<rect x="{status_x - 2:.2f}" y="{status_y - LFS + 1:.2f}" '
           f'width="{lw - PAD - (status_x - lx):.2f}" height="{LFS + 2}" fill="{COL["bg"]}"/>'
           + text_el(status_x, status_y, [(label, "co")], LCW))
        for k, (_, _, label) in enumerate(status_events))

    def status_overlay(offset, period=None):
        return layer([(s + offset, e + offset) for s, e, _ in status_events], status_slots,
                     [OFF * (k + 1) for k in range(len(status_events))], period)

    status.append(status_overlay(0))

    command_text = text_el(tx, command_y + TLH * 0.74, p + [(session[0][0], "cc")], TCW)
    left_command = text_el(lx + PAD, ly + BAR + 24,
                           prompt("~/eye") + [("./eye --ascii --watch", "cc")], LCW)

    def strip_rows(n, top, height):
        rows = [r for r in range(EYE_ROWS) if top - 0.4 * EFS < ey + (r + 0.8) * ECH < top + height + EFS]
        return f'<g class="e">{eye_svg(frame_cells[n], ex, ey, rows)}</g>'

    windows = ((lx, ly, lw, eye_h), (rx, ry, RIGHT_W, term_h))
    glitch_chars_array = tuple(glitch_chars)
    glitch_colors = ("#58a6ff", "#7ee7f5", "#f0f6fc", "#1f6feb", "#ff2bd6", "#ff3b5c")
    glitch_events = []
    for index, spawned_at in enumerate(spawn_times):
        intensity = 1 + 0.55 * index
        for subframe in range(3):
            start_at = spawned_at + subframe * 0.07
            glitch_events.append((start_at, start_at + 0.07, intensity, index))
    for subframe in range(6):
        start_at = overload_at + subframe * 0.08
        glitch_events.append((start_at, start_at + 0.08, 5.5, len(spawn_times)))

    nick_spans, shake_events, glitch_log = [], [], []
    strip_clip_index = 0
    for start_at, end_at, intensity, burst in glitch_events:
        nick_spans.append((start_at, end_at, 3 + 1.4 * intensity))
        overlays = []
        for window_index, (win_x, win_y, win_w, win_h) in enumerate(windows):
            direction = 1 if window_index == 0 else -1
            # two bands per window at most: each band copies part of the window, which made the image heavy
            for _ in range(min(2, int(1 + intensity))):
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
                head = (f'<rect x="{win_x}" y="{strip_y:.2f}" width="{win_w}" height="{strip_h:.2f}" '
                        f'fill="#0d1117"/><g clip-path="url(#{clip_id})"><g>')
                if window_index == 0:
                    baseline = ly + BAR + 24
                    tail = (left_command.replace(f'x="{num(lx + PAD, 1)}"', f'x="{num(lx + PAD + dx, 1)}"', 1)
                            if strip_y <= baseline <= strip_y + strip_h else "")
                    overlays.append((0, (head, strip_y, strip_h, tail + "</g></g>")))
                    continue
                # the shifted prompt line only matters where its glyphs reach the strip
                baseline = command_y + TLH * 0.74
                content = (command_text.replace(f'x="{num(tx, 1)}"', f'x="{num(tx + dx, 1)}"', 1)
                           if strip_y - 10 < baseline < strip_y + strip_h + 24 else "")
                for kind, top, height, segs in strip_output_parts:
                    if kind == "text":
                        baseline = top + height * 0.74
                        if strip_y <= baseline <= strip_y + strip_h:
                            content += text_el(tx + dx, baseline, segs, TCW)
                    else:
                        for row_index, row_text in enumerate(banner):
                            row_y = top + row_index * height
                            if row_y <= strip_y + strip_h and row_y + height >= strip_y:
                                content += banner_svg([row_text], tx + dx, row_y, bcw, height, 0,
                                                      animated=False, row_offset=row_index)
                overlays.append((1, head + content + "</g></g>"))

            for _ in range(1 + int(intensity / 2)):
                gy = rng.uniform(win_y + BAR + 2, win_y + win_h - 2)
                color = rng.choice(("#00e5ff", "#ff2bd6"))
                overlays.append((window_index, f'<rect x="{win_x}" y="{gy:.2f}" width="{win_w}" height="1.2" '
                                               f'fill="{color}" opacity="0.65"/>'))
        for _ in range(int(2 + intensity)):
            window_index = rng.choice((0, 1))
            win_x, win_y, win_w, win_h = windows[window_index]
            text = "".join(rng.choice(glitch_chars_array) for _ in range(rng.randint(3, 10)))
            gx = rng.uniform(win_x + 2, win_x + win_w - 48)
            gy = rng.uniform(win_y + BAR + 10, win_y + win_h - 4)
            color = rng.choice(glitch_colors)
            size = rng.choice((8.4, 12.2))
            overlays.append((window_index, f'<text x="{gx:.2f}" y="{gy:.2f}" font-size="{size}" '
                                           f'fill="{color}">{esc(text)}</text>'))
        glitch_log.append((start_at, end_at, 2 + 0.9 * intensity, burst, overlays))
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
        shake_points.append((time, f"transform:translate({dx:.2f}px,{dy:.2f}px)"))

    # the idle repeat glitches only the eye window and needs its own random mini glitches
    idle_markup = [mini_window(spec, mini_cells(spec[0], spec[1], idle_period), idle_period, idle_period)
                   for spec in minis]
    mini_markup += idle_markup
    status.append(status_overlay(idle_period, idle_period))

    def ghost_copy(n, spans, look, sign, period):
        shifts = {s for *_, s in spans}
        if len(shifts) == 1:
            return f'<use href="#e{n}" {look} x="{num(sign * shifts.pop())}"/>'
        start, stop = spans[0][0], spans[-1][1]
        moves = steps([(a, b, f"transform:translate({num(sign * s)}px)") for a, b, s in spans],
                      "transform:none", start)
        return f'<use href="#e{n}" {look} style="{timing(moves, start, stop, period)}"/>'

    def glitch_pass(offset, period=None):
        ghost_frames, red_spans, bands, rest = {}, {}, {}, {}
        for event_index, (start_at, end_at, eye_shift, burst, overlays) in enumerate(glitch_log):
            items = [item for window_index, item in overlays if not (period and window_index)]
            # the eye-window bands come first in every glitch, so they can follow the eye frame by frame
            # while lines, text and terminal bands stay one copy per glitch
            slots, spans = rest.setdefault(burst, ({}, {}))
            slots[event_index] = "".join(item for item in items if isinstance(item, str))
            spans[event_index] = [(start_at + offset, end_at + offset)]
            for n, a, b in segments(start_at + offset, end_at + offset):
                ghost_frames.setdefault(n, []).append((a, b, eye_shift))
                red_spans.setdefault(n, []).append((a, b))
                slots, spans = bands.setdefault(burst, ({}, {}))
                if (event_index, n) not in slots:
                    slots[(event_index, n)] = "".join(item[0] + strip_rows(n, item[1], item[2]) + item[3]
                                                      for item in items if not isinstance(item, str))
                spans.setdefault((event_index, n), []).append((a, b))
        # one pair of copies per eye frame; a frame seen at several glitch strengths moves its copies instead.
        # The filters only run while a glitch shows the copy, for about 70 ms at a time.
        ghosts = "".join(layer([(a, b) for a, b, _ in spans],
                               ghost_copy(n, spans, 'filter="url(#tC)" opacity="0.8"', -1, period)
                               + ghost_copy(n, spans, 'filter="url(#tM)" opacity="0.85"', 1, period), None, period)
                         for n, spans in ghost_frames.items())
        reds = "".join(layer(spans, f'<use href="#e{n}" class="rd"/>', None, period) for n, spans in red_spans.items())
        tops = "".join(sprite(*bands[burst], period) + sprite(*rest[burst], period) for burst in rest)
        return ghosts, reds, tops, set(red_spans)

    first, idle = glitch_pass(0), glitch_pass(idle_period, idle_period)
    ghosts, reds, tops = (first[i] + idle[i] for i in range(3))
    copied = first[3] | idle[3]
    nicks = "".join(
        track([(a, b, f"opacity:{opacity};transform:translate({num(sign * s)}px)") for a, b, s in nick_spans],
              "opacity:0", ' class="o"', text_el(tx, command_y + TLH * 0.74, [(HANDLE, None)], TCW, f'fill="{color}"'))
        for color, sign, opacity in (("#00e5ff", -1, 0.85), ("#ff2bd6", 1, 0.9)))

    eye_colors = {f"s{i}": c for i, c in enumerate(SCLERA)} | {f"i{i}": c for i, c in enumerate(IRIS)} \
        | {"hl": SHINE, "vn": VEIN, "lu": LID_UP, "ll": LID_LO}

    def palette(tint):
        return ";".join(f"--{k}:{tint(c)}" for k, c in eye_colors.items())

    intro_spans, loop_spans = frame_spans(seq_i, t_intro), frame_spans(seq_l, t_loop)
    start_id = frame_ids[(0, 0, 1.0)]

    def eye_frame(n):
        rows = eye_svg(frame_cells[n], ex, ey)
        if n in copied:
            rows = f'<g id="e{n}" class="e">{rows}</g>'
        # opacity for eye frames: they flip often, and an opacity flip is the cheapest change to repaint
        loop = (animation(steps(loop_spans[n], "opacity:0"), t_loop, t_intro, True) if n in loop_spans
                else animation([(0.0, "opacity:0"), (1.0, "opacity:0")], 1, t_intro, fill="forwards"))
        intro = animation(steps(intro_spans.get(n, []), "opacity:0") + [(t_intro, "opacity:1")], t_intro,
                          fill="forwards")
        return f'<g class="fr{" fs" if n == start_id else ""}" style="{intro}"><g style="{loop}">{rows}</g></g>'

    eyes = f'<g class="e">{"".join(eye_frame(n) for n in range(len(order)))}</g>'
    shake = animation(shake_points, scene_end)

    body = [
        window(lx, ly, lw, eye_h, f"eye — ascii — {EYE_COLS}×{EYE_ROWS}"),
        window(rx, ry, RIGHT_W, term_h, f"{HANDLE}@github: ~ — zsh — 80×24"),
        f'<g class="l">{"".join(left)}</g>',
        ghosts,
        nicks,
        f'<g class="t" clip-path="url(#clipT)">{"".join(term)}</g>',
        eyes,
        reds,
        "".join(mini_markup),
        f'<g class="l">{"".join(status)}</g>',
        window_border(rx, ry, RIGHT_W, term_h),
        window_border(lx, ly, lw, eye_h),
        tops,
    ]

    term_colors = {"cu": COL["user"], "cs": COL["sym"], "ch": COL["host"], "cp": COL["path"],
                   "cc": COL["cmd"], "cm": COL["dim"], "co": COL["text"], "cn": COL["cmd"], "lv": COL["live"]}
    mini_tints = ";".join(f"--s{i}:{SCLERA[min(i + 1, len(SCLERA) - 1)]};--i{i}:{IRIS[min(i + 1, len(IRIS) - 1)]}"
                          for i in range(len(SCLERA)))
    style = (f"text{{font-family:{FONT};white-space:pre;fill:{COL['text']}}}"
             f".e text{{font-size:{EFS}px}}.t text{{font-size:{TFS}px}}.l text{{font-size:{LFS}px}}"
             ".mini text{font-weight:700}"
             f".wt{{font-size:12px!important;fill:{COL['title']}!important;white-space:normal}}"
             ".cn{font-weight:700}"
             + "".join(f".{k}{{fill:var(--{k},{v})}}" for k, v in eye_colors.items())
             + "".join(f".{k}{{fill:{v}}}" for k, v in term_colors.items())
             + f".mini{{{mini_tints}}}"
             + f".rd{{{palette(red_tint)}}}"
             ".gc{fill:#7ee7f5}.fr,.o,.h{opacity:0}"
             ".on{animation-name:on;animation-timing-function:step-end;animation-fill-mode:both}"
             "@keyframes on{from{opacity:0}to{opacity:1}}"
             ".cw{opacity:0;animation-name:cw;animation-timing-function:step-end;animation-fill-mode:both}"
             "@keyframes cw{from{opacity:1}to{opacity:0}}"
             ".cur,.lv{animation:bl 1.1s step-end infinite}@keyframes bl{0%{opacity:1}50%{opacity:0}}"
             "@media(prefers-reduced-motion:reduce){*{animation:none!important}.fs{opacity:1}}"
             + "".join(css) + "".join(f"@keyframes {name}{{{kf}}}" for kf, name in keyframe_names.items()))
    clip = (f'<clipPath id="clipT"><rect x="{rx}" y="{ry + BAR + 1}" width="{RIGHT_W}" '
            f'height="{term_h - BAR - 1}" rx="10"/></clipPath>')
    filters = (
        '<filter id="tC" x="-5%" y="-5%" width="110%" height="110%" '
        'color-interpolation-filters="sRGB"><feColorMatrix type="matrix" values="'
        '0 0 0 0 0  0 0 0 0 0.9  0 0 0 0 1  .5 .5 .5 0 -.12"/></filter>'
        '<filter id="tM" x="-5%" y="-5%" width="110%" height="110%" '
        'color-interpolation-filters="sRGB"><feColorMatrix type="matrix" values="'
        '0 0 0 0 1  0 0 0 0 0.17  0 0 0 0 0.84  .5 .5 .5 0 -.12"/></filter>')
    # the shake moves the root element: moving a group instead makes every frame inside it costlier to repaint
    return (f'<svg style="{shake}" '
            f'xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
            f'xml:space="preserve" role="img" aria-label="{html.escape(alt_text())}">'
            f'<title>{esc(FIRST_NAME)} {esc(LAST_NAME)}</title>'
            f'<defs>{clip}{filters}{"".join(extra_defs)}</defs><style>{style}</style>'
            + "".join(body) + "</svg>"), len(order)


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
