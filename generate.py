from __future__ import annotations

import datetime as dt
import functools
import html
import math
import pathlib
import re
import sys
from zoneinfo import ZoneInfo

FIRST_NAME = "Ruslan"
LAST_NAME = "Murha"
HANDLE = "mvrha"
BANNER = "MVRHA"
TIMEZONE = "Europe/Warsaw"
OUT_DIR = pathlib.Path(__file__).resolve().parent / "assets"

FONT = ("ui-monospace,'SF Mono',SFMono-Regular,Menlo,Consolas,"
        "'Liberation Mono','DejaVu Sans Mono',monospace")
COL = {
    "bg": "#0c0d10", "bar": "#15171c", "sep": "#23272e", "border": "#2c3139",
    "title": "#7d8590", "text": "#d4cfc5", "dim": "#6b7079", "cmd": "#f2eee6",
    "user": "#f0a35e", "host": "#d9b27c", "path": "#8fb3d9", "sym": "#7d8590",
    "cursor": "#f0a35e", "live": "#ff5f57",
}
BANNER_COLORS = ["#fcd59a", "#f6b46d", "#ec9550", "#d9743a", "#bf5a26", "#9a4519"]
BANNER_SHADOW = "#4a2210"
SCLERA = ["#2a2723", "#423d37", "#5e584f", "#7e776b", "#a19a8c"]
IRIS = ["#4a1c09", "#6e2d0f", "#9a4216", "#c4591f", "#e2762f", "#f39a4f", "#fcc683"]
SHINE, VEIN, LID_UP, LID_LO = "#fff8ec", "#8f4636", "#8a6440", "#5f4a36"

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
            f'lengthAdjust="spacingAndGlyphs"{attrs}>{body}</text>')


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


def banner_svg(rows, x, y, cw, rh, t0):
    parts = []
    for i, row in enumerate(rows):
        yy = y + i * rh
        main, shadow = [], []
        for m in re.finditer("█+", row):
            bx, bw = x + m.start() * cw, (m.end() - m.start()) * cw
            shadow.append(f'<rect x="{bx + 2:.1f}" y="{yy + 2:.1f}" width="{bw:.1f}" height="{rh:.1f}"/>')
            main.append(f'<rect x="{bx:.1f}" y="{yy:.1f}" width="{bw:.1f}" height="{rh:.1f}"/>')
        parts.append(f'<g class="on" style="animation-duration:{t0 + i * 0.04:.3f}s" shape-rendering="crispEdges">'
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


LEFT_W, RIGHT_W, WIN_H, MARGIN, GAP, BAR, PAD = 350, 484, 330, 6, 14, 30, 14
TFS, TCW, TLH = 12.2, 7.35, 17.4
BANNER_CW, BANNER_ASPECT = 10.0, 1.93
LFS, LCW = 11, 6.6
EYE_TOP = BAR + 30


def build(wide: bool) -> tuple[str, int]:
    if wide:
        W, H = MARGIN * 2 + LEFT_W + GAP + RIGHT_W, MARGIN * 2 + WIN_H
        lx, ly, lw = MARGIN, MARGIN, LEFT_W
        rx, ry = MARGIN + LEFT_W + GAP, MARGIN
        gaze_scale = (1000.0, 650.0)
    else:
        W, H = MARGIN * 2 + RIGHT_W, MARGIN * 2 + WIN_H * 2 + GAP
        lx, ly, lw = MARGIN, MARGIN, RIGHT_W
        rx, ry = MARGIN, MARGIN + WIN_H + GAP
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
                w = max(len(row) for row in banner) * bcw
                marks["banner"] = (tx + w / 2, y + lh / 2)
                delay += 0.04 * len(banner)
            else:
                w = sum(len(s) for s, _ in segs) * TCW
                if segs is name:
                    marks["name"] = (tx + w / 2, y + lh / 2)
                term.append(f'<g class="on" style="animation-duration:{delay:.3f}s">'
                            + text_el(tx, y + lh * 0.74, segs, TCW) + "</g>")
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
        eyes.append(f'<g class="fr f{n}{start}">{eye_svg(render_eye(gx, gy, k), ex, ey)}</g>')
    status_y = ey + EH + 16
    status = [text_el(lx + PAD, status_y, [("●", "lv")], LCW),
              text_el(lx + PAD + 2 * LCW, status_y, [("live", "cm"), (" · ", "cs")], LCW)]
    for n, (label, sp) in enumerate(labels.items()):
        css.append(keyframes(f"si{n}", sp["i"], t_intro))
        css.append(keyframes(f"sl{n}", sp["l"], t_loop))
        css.append(f".lb{n}{{animation:sl{n} {t_loop}s step-end {phase}s infinite,si{n} {t_intro}s step-end}}")
        start = " fs" if label == "watching you" else ""
        status.append(f'<g class="fr lb{n}{start}">'
                      + text_el(lx + PAD + 9 * LCW, status_y, [(label, "co")], LCW) + "</g>")

    body = [
        window(rx, ry, RIGHT_W, WIN_H, f"{HANDLE}@github: ~ — zsh — 80×24"),
        f'<g class="t" clip-path="url(#clipT)">{"".join(term)}</g>',
        window_border(rx, ry, RIGHT_W, WIN_H),
        window(lx, ly, lw, WIN_H, f"eye — ascii — {EYE_COLS}×{EYE_ROWS}"),
        f'<g class="e">{"".join(eyes)}</g><g class="l">{"".join(left)}{"".join(status)}</g>',
        window_border(lx, ly, lw, WIN_H),
    ]

    classes = {f"s{i}": c for i, c in enumerate(SCLERA)} | {f"i{i}": c for i, c in enumerate(IRIS)} \
        | {"hl": SHINE, "vn": VEIN, "lu": LID_UP, "ll": LID_LO, "cu": COL["user"], "cs": COL["sym"],
           "ch": COL["host"], "cp": COL["path"], "cc": COL["cmd"], "cm": COL["dim"], "co": COL["text"],
           "cn": COL["cmd"], "lv": COL["live"]}
    style = (f"text{{font-family:{FONT};white-space:pre;fill:{COL['text']}}}"
             f".e text{{font-size:{EFS}px}}.t text{{font-size:{TFS}px}}.l text{{font-size:{LFS}px}}"
             f".wt{{font-size:12px!important;fill:{COL['title']}!important;white-space:normal}}"
             ".cn{font-weight:700}"
             + "".join(f".{k}{{fill:{v}}}" for k, v in classes.items())
             + ".fr{opacity:0}.fs{opacity:1}"
             ".on{animation-name:on;animation-timing-function:step-end;animation-fill-mode:both}"
             "@keyframes on{from{opacity:0}to{opacity:1}}"
             ".cw{opacity:0;animation-name:cw;animation-timing-function:step-end;animation-fill-mode:both}"
             "@keyframes cw{from{opacity:1}to{opacity:0}}"
             ".cur,.lv{animation:bl 1.1s step-end infinite}@keyframes bl{0%{opacity:1}50%{opacity:0}}"
             + "".join(css))
    clip = (f'<clipPath id="clipT"><rect x="{rx}" y="{ry + BAR + 1}" width="{RIGHT_W}" '
            f'height="{WIN_H - BAR - 1}" rx="10"/></clipPath>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
            f'xml:space="preserve" role="img" aria-label="{esc(FIRST_NAME)} {esc(LAST_NAME)} — terminal">'
            f'<title>{esc(FIRST_NAME)} {esc(LAST_NAME)}</title><defs>{clip}</defs><style>{style}</style>'
            + "".join(body) + "</svg>"), len(frames)


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for file, wide in (("terminal.svg", True), ("terminal-mobile.svg", False)):
        svg, n_frames = build(wide)
        (OUT_DIR / file).write_text(svg, encoding="utf-8")
        print(f"{file}: {len(svg.encode()) / 1024:.0f} KB, {n_frames} eye frames")
