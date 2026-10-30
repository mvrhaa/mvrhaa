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
T = dict(
    bg="#0d1117", bar="#161b22", sep="#21262d", border="#30363d",
    lights=("#ff5f57", "#febc2e", "#28c840"),
    title="#7d8590", text="#c9d1d9", dim="#6e7681", cmd="#f0f6fc", user="#58a6ff", host="#8b949e",
    path="#c9d1d9", sym="#6e7681", cursor="#58a6ff", live="#58a6ff", accent="#58a6ff", accent2="#58a6ff",
    banner=((0, "#f0f6fc"), (0.5, "#b1bac4"), (1, "#6e7681")), banner_shadow="#1b2a3e",
    sclera=((0, "#8b929c"), (0.45, "#686f79"), (0.8, "#343a42"), (1, "#8b949e")),
    iris=((0.38, "#0a1a2e"), (0.46, "#3474b3"), (0.6, "#93bde8"), (0.8, "#3474b3"), (1, "#1a3f6b")),
    shine="#f2f8ff",
    ghost=(("#06505c", "#00e5ff"), ("#5a124c", "#ff2bd6")),
    red=("#820b1a", "#ff1b3a", "#ff2d5e"),
    glitch=("#00e5ff", "#ff2bd6", "#58a6ff"),
    glow="#1f6feb",
)

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
EYE_TOP_ROW, EYE_BOTTOM_ROW = 2, 24

TFS, TCW, TLH, BAR, PAD, LFS, LCW = 12.2, 7.35, 17.4, 30, 14, 11, 6.6
BANNER_ASPECT = 1.93
HIDE, SHOW = "visibility:hidden", "visibility:visible"
OFF = 1000


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
                cells[(r, c)] = (ch, "ir")
                continue
            v = 0.74 * (0.30 + 0.70 * n[2] ** 0.65)
            if rr < 1.2:
                v *= 0.66 + 0.34 * _smooth(1.0, 1.2, rr)
            v = min(0.999, max(0.0, v * shade + jit * 0.05))
            u = abs(px - X0) / A
            if u > 0.6 and _hash(c, r, 7) < 0.05 * (u - 0.6) / 0.4:
                cells[(r, c)] = ("~", "sc")
                continue
            idx = int(v * (len(SCLERA_RAMP) - 1) + jit * 1.2)
            cells[(r, c)] = (SCLERA_RAMP[max(0, min(len(SCLERA_RAMP) - 1, idx))], "sc")
    for key, val in _lid_cells(k).items():
        cells.setdefault(key, val)
    return cells


def _lid_cells(k: float) -> dict:
    closed = k < 0.06
    cells = {}
    for which in (0, 1):
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
            cells.setdefault((r, c), (ch, "sc"))
            pr = rows.get(c - 1)
            rows[c] = r
            if pr is not None and abs(pr - r) > 1:
                outer = c - 1 if (c - 0.5) * ECW < X0 else c
                fill = "/" if pr > r else "\\"
                for rr in range(min(pr, r) + 1, max(pr, r)):
                    cells.setdefault((rr, outer), (fill, "sc"))
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
        runs = [c for _, c in segs]
        base = max(dict.fromkeys(runs), key=runs.count)
        attrs = f'class="{base}" {attrs}'
    body = "".join(f'<tspan class="{c}">{esc(t)}</tspan>' if c and c != base else esc(t) for t, c in segs)
    return (f'<text x="{num(x, 1)}" y="{num(y, 1)}" textLength="{num(n * cw, 1)}" '
            f'lengthAdjust="spacingAndGlyphs"{(" " + attrs.strip()) if attrs else ""}>{body}</text>')


def steps(spans, idle, origin=0.0):
    out, end = [(0.0, idle)], None
    for start, stop, value in spans:
        if end is not None and start > end + 1e-9:
            out.append((end - origin, idle))
        out.append((start - origin, value))
        end = stop
    return out + ([(end - origin, idle)] if end is not None else [])


def with_tweens(seq):
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


def eye_rows(cells):
    out = []
    for r in range(EYE_ROWS):
        kinds = {}
        for c in range(EYE_COLS):
            cell = cells.get((r, c))
            if cell:
                kinds.setdefault(cell[1], []).append(c)
        for kind in ("sc", "ir", "hl"):
            cols = kinds.get(kind)
            if not cols:
                continue
            own = set(cols)
            line = "".join(cells[(r, c)][0] if c in own else " " for c in range(cols[0], cols[-1] + 1))
            out.append(text_el(cols[0] * ECW, r * ECH + ECH * 0.8, [(line, kind)], ECW))
    return "".join(out)


def stops_of(stops):
    return "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops)


def iris_gradient(gid, gx, gy):
    gv = _norm((gx, gy, 1.0))
    ring = R * math.cos(TH_I)
    cx, cy = X0 + ring * gv[0], Y0 + ring * gv[1]
    angle = math.degrees(math.atan2(gv[1], gv[0]))
    return (f'<radialGradient id="{gid}" gradientUnits="userSpaceOnUse" cx="0" cy="0" r="1" '
            f'gradientTransform="translate({cx:.2f} {cy:.2f}) rotate({angle:.1f}) '
            f'scale({IRIS_R * gv[2]:.2f} {IRIS_R:.2f})">' + stops_of(T["iris"]) + "</radialGradient>")


def sclera_gradient():
    return (f'<radialGradient id="gS" gradientUnits="userSpaceOnUse" cx="0" cy="0" r="1" '
            f'gradientTransform="translate({X0:.1f} {Y0 - 6:.1f}) scale({A:.1f} {(HU + HL) / 2:.1f})">'
            + stops_of(T["sclera"]) + "</radialGradient>")


def prompt(path="~"):
    return [(HANDLE, "cu"), ("@", "cs"), ("github", "ch"), (" ", None), (path, "cp"), (" % ", "cs")]


PLEN = sum(len(s) for s, _ in prompt())


class Doc:
    def __init__(self):
        self.css, self.defs, self.kf = [], [], {}
        self.n = 0

    def uid(self, prefix):
        self.n += 1
        return f"{prefix}{self.n}"

    def anim(self, changes, duration, delay=0.0, infinite=False, fill=""):
        body = "".join(f"{k}{{{v}}}" for k, v in
                       {f"{100 * t / duration:.4g}%": v for t, v in changes}.items())
        name = self.kf.setdefault(body, f"k{len(self.kf)}")
        return (f"{name} {num(duration)}s step-end" + (f" {num(delay)}s" if delay else "")
                + (" infinite" if infinite else "") + (f" {fill}" if fill else ""))

    def layer(self, spans, inner, period=None):
        start, stop = spans[0][0], spans[-1][1]
        changes = steps([(a, b, SHOW) for a, b in spans], HIDE, start)
        rule = self.anim(changes, period, start, True) if period else self.anim(changes, stop - start, start)
        return f'<g class="h" style="animation:{rule}">{inner}</g>'

    def appear(self, t, inner):
        return f'<g class="on" style="animation-duration:{t:.3f}s">{inner}</g>'

    def typed(self, x, y, segs, cmd, t_show, t_type):
        plen = sum(len(s) for s, _ in segs)
        typing = len(cmd) * 0.065
        t_enter = t_type + typing + 0.22
        cx, move = x + plen * TCW, len(cmd) * TCW
        name = self.uid("ty")
        self.css.append(f"@keyframes {name}{{0%{{transform:translateX(0)}}"
                        f"{100 * t_type / (t_type + typing):.4g}%{{transform:translateX(0);"
                        f"animation-timing-function:steps({len(cmd)},end)}}"
                        f"100%{{transform:translateX({move:.1f}px)}}}}")
        markup = self.appear(t_show, text_el(x, y + TLH * 0.74, segs + [(cmd, "cc")], TCW)
                             + f'<g transform="translate({move:.1f},0)" style="animation:{name} '
                               f'{t_type + typing:.3f}s linear both">'
                             + f'<rect x="{cx:.1f}" y="{y:.1f}" width="{move + TCW + 1:.1f}" height="{TLH:.1f}" '
                               f'fill="{T["bg"]}"/>'
                             + f'<g class="cw" style="animation-duration:{t_enter:.2f}s">'
                               f'<rect x="{cx:.1f}" y="{y + 2:.1f}" width="{TCW:.1f}" height="{TLH - 3:.1f}" '
                               f'class="cb"/></g></g>')
        return markup, t_enter, (cx + move / 2, y + TLH / 2)

    def banner(self, rows, x, y, cw, rh, t0=None):
        if "gB" not in "".join(self.defs):
            self.defs.append(f'<linearGradient id="gB" gradientUnits="userSpaceOnUse" x1="0" y1="{y:.1f}" '
                             f'x2="0" y2="{y + len(rows) * rh:.1f}">' + stops_of(T["banner"]) + "</linearGradient>")
        parts = []
        for i, row in enumerate(rows):
            yy = y + i * rh
            main, shadow = [], []
            for m in re.finditer("█+", row):
                bx, bw = x + m.start() * cw, (m.end() - m.start()) * cw
                shadow.append(f'<rect x="{bx + 2:.1f}" y="{yy + 2:.1f}" width="{bw:.1f}" height="{rh:.1f}"/>')
                main.append(f'<rect x="{bx:.1f}" y="{yy:.1f}" width="{bw:.1f}" height="{rh:.1f}"/>')
            body = (f'<g fill="{T["banner_shadow"]}">{"".join(shadow)}</g>'
                    f'<g fill="url(#gB)">{"".join(main)}</g>')
            parts.append(self.appear(t0 + i * 0.04, body) if t0 is not None else body)
        return f'<g shape-rendering="crispEdges">{"".join(parts)}</g>'

    def window(self, x, y, w, h, title):
        r = 10
        dots = "".join(f'<circle cx="{x + cx}" cy="{y + BAR / 2}" r="5.5" fill="{c}"/>'
                       for cx, c in zip((18, 36, 54), T["lights"]))
        return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{T["bg"]}"/>'
                f'<path d="M{x + r} {y}h{w - 2 * r}a{r} {r} 0 0 1 {r} {r}v{BAR - r}h{-w}v{r - BAR}'
                f'a{r} {r} 0 0 1 {r} {-r}z" fill="{T["bar"]}"/>'
                f'<path d="M{x} {y + BAR + 0.5}h{w}" stroke="{T["sep"]}"/>' + dots
                + f'<text x="{x + w / 2}" y="{y + 19}" text-anchor="middle" class="wt">{esc(title)}</text>')

    @staticmethod
    def border(x, y, w, h):
        return (f'<rect x="{x + 0.5}" y="{y + 0.5}" width="{w - 1}" height="{h - 1}" rx="9.5" '
                f'fill="none" stroke="{T["border"]}"/>')


class Eye:
    def __init__(self, doc, ox, oy, scale, gaze_scale):
        self.doc, self.ox, self.oy, self.s = doc, ox, oy, scale
        self.cx, self.cy = ox + scale * X0, oy + scale * Y0
        self.gaze_scale = gaze_scale

    def gaze(self, px, py):
        gx, gy = (px - self.cx) / self.gaze_scale[0], (py - self.cy) / self.gaze_scale[1]
        m = math.hypot(gx, gy)
        if m > 0.55:
            gx, gy = gx * 0.55 / m, gy * 0.55 / m
        gy = min(0.32, max(-0.22, gy))
        return round(gx * 20) / 20, round(gy * 20) / 20

    @staticmethod
    def blink(t0, gx, gy, after):
        lids = (0.7, 0.4, 0.15, 0.0)
        closing = [(t0 + i * 0.03, (gx, gy, k, "blink")) for i, k in enumerate(lids)]
        opening = [(t0 + 0.16 + i * 0.03, (gx, gy, k, "blink")) for i, k in enumerate(lids[-2::-1])]
        return closing + opening + [(t0 + 0.25, (gx, gy, 1.0, after))]

    def plan(self, looks, t_final, glances):
        lids = (0.7, 0.4, 0.15, 0.0)
        intro = [(0.0, (0, 0, 0.0, "waking up"))]
        intro += [(0.35 + i * 0.045, (0, 0, k, "waking up")) for i, k in enumerate(lids[-2::-1])]
        intro.append((0.5, (0, 0, 1.0, "watching you")))
        for t, px, py, k, label in looks:
            intro.append((t, (*self.gaze(px, py), k, label)))
        intro.append((t_final + 1.0, (0, 0, 1.0, "watching you")))
        intro += self.blink(t_final + 1.7, 0, 0, "watching you")
        self.t_intro = round(t_final + 2.6, 2)

        first, second = self.gaze(*glances[0]), self.gaze(*glances[1])
        loop = [(0.0, (0, 0, 1.0, "watching you")),
                (1.8, (-0.45, 0.05, 1.0, "looking around")),
                (2.9, (-0.35, -0.2, 1.0, "looking around")),
                (3.7, (0, 0, 1.0, "watching you"))]
        loop += self.blink(4.3, 0, 0, "watching you")
        loop += [(5.6, (*first, 1.0, "reading the terminal")),
                 (6.8, (*second, 1.0, "reading the terminal")),
                 (7.8, (0, 0, 1.0, "watching you")),
                 (8.8, (-0.25, 0.3, 1.0, "looking around")),
                 (9.7, (0, 0, 1.0, "watching you"))]
        loop += self.blink(10.3, 0, 0, "watching you") + self.blink(10.75, 0, 0, "watching you")
        loop += [(11.6, (0.3, -0.2, 1.0, "looking around")),
                 (12.5, (0, 0, 1.0, "watching you"))]
        self.t_loop = 13.6

        self.seq_i, self.seq_l = with_tweens(sorted(intro)), with_tweens(sorted(loop))
        self.order = list(dict.fromkeys(tuple(st[:3]) for _, st in self.seq_i + self.seq_l))
        self.labels = list(dict.fromkeys(st[3] for _, st in self.seq_i + self.seq_l))
        self.frame_ids = {state: n for n, state in enumerate(self.order)}
        self.cells = {n: render_eye(*state) for n, state in enumerate(self.order)}
        gazes = list(dict.fromkeys(state[:2] for state in self.order))
        self.grad = {n: gazes.index(state[:2]) for n, state in enumerate(self.order)}
        self.doc.defs.append(sclera_gradient())
        self.doc.defs += [iris_gradient(f"gI{j}", gx, gy) for j, (gx, gy) in enumerate(gazes)]

    def shown_frame(self, at):
        local, seq = (at, self.seq_i) if at < self.t_intro else ((at - self.t_intro) % self.t_loop, self.seq_l)
        state = seq[0][1]
        for t, st in seq:
            if t > local:
                break
            state = st
        return self.frame_ids[tuple(state[:3])]

    def frames(self):
        doc = self.doc

        def spans(seq, total):
            out = {}
            for i, (t0, st) in enumerate(seq):
                t1 = seq[i + 1][0] if i + 1 < len(seq) else total
                out.setdefault(self.frame_ids[tuple(st[:3])], []).append((t0, t1, SHOW))
            return out

        intro_spans, loop_spans = spans(self.seq_i, self.t_intro), spans(self.seq_l, self.t_loop)
        start = self.frame_ids[(0, 0, 1.0)]
        out = []
        for n in range(len(self.order)):
            loop = (doc.anim(steps(loop_spans[n], HIDE), self.t_loop, self.t_intro, True) if n in loop_spans
                    else doc.anim([(0.0, HIDE), (1.0, HIDE)], 1, self.t_intro, fill="forwards"))
            intro = doc.anim(steps(intro_spans.get(n, []), HIDE) + [(self.t_intro, SHOW)], self.t_intro,
                             fill="forwards")
            out.append(f'<g class="fr{" fs" if n == start else ""}" style="animation:{intro}">'
                       f'<g style="animation:{loop};--ir:url(#gI{self.grad[n]})">'
                       f'<g id="e{n}" class="e">{eye_rows(self.cells[n])}</g></g></g>')
        return "".join(out)

    def label_track(self, x, y):
        doc = self.doc
        order = ["watching you"] + [k for k in self.labels if k != "watching you"]
        pos = {k: OFF * i for i, k in enumerate(order)}

        def shift(v):
            return f"transform:translate({num(-v)}px)" if v else "transform:none"

        intro = [(t, shift(pos[st[3]])) for t, st in self.seq_i]
        loop = [(t, shift(pos[st[3]])) for t, st in self.seq_l]
        inner = "".join(text_el(x + pos[k], y, [(k, "co")], LCW) for k in order)
        return (f'<g style="animation:{doc.anim(intro, self.t_intro)}">'
                f'<g style="animation:{doc.anim(loop, self.t_loop, self.t_intro, True)}">{inner}</g></g>')

    def open(self):
        scale = f" scale({self.s})" if self.s != 1 else ""
        return f'<g class="E" transform="translate({num(self.ox, 2)} {num(self.oy, 2)}){scale}">'


def glitch(doc, eye, bursts, idle, regions, rng):
    back, eye_front, page_front, shakes = [], [], [], []
    period, idle_bursts = idle
    runs = [(b, None) for b in bursts] + [(b, period) for b in idle_bursts]
    for (t0, count, step, strength), per in runs:
        shake = []
        for i in range(count):
            a, b = t0 + i * step, t0 + (i + 1) * step
            n = eye.shown_frame((a + b) / 2)
            j = eye.grad[n]
            dx = rng.uniform(2.0, 3.0 + 1.4 * strength)
            back.append(doc.layer([(a, b)], f'<use href="#e{n}" class="gC" x="{-dx:.1f}" opacity=".8"/>'
                                            f'<use href="#e{n}" class="gM" x="{dx * 0.8:.1f}" opacity=".85"/>', per))
            front = f'<use href="#e{n}" class="rd"/>' if strength >= 4 else ""
            ex0, ew = regions["eye"]
            for _ in range(1 if strength < 2.5 else 2):
                sh = rng.uniform(5, 9 + 2.2 * strength)
                sy = rng.uniform(EYE_TOP_ROW * ECH, EYE_BOTTOM_ROW * ECH - sh)
                cid = doc.uid("c")
                doc.defs.append(f'<clipPath id="{cid}"><rect x="{ex0:.1f}" y="{sy:.1f}" width="{ew:.1f}" '
                                f'height="{sh:.1f}"/></clipPath>')
                sdx = rng.choice((-1, 1)) * rng.uniform(3, 4 + 3.2 * strength)
                front += (f'<rect x="{ex0:.1f}" y="{sy:.1f}" width="{ew:.1f}" height="{sh:.1f}" fill="{T["bg"]}"/>'
                          f'<g clip-path="url(#{cid})"><use href="#e{n}" x="{sdx:.1f}" '
                          f'style="--ir:url(#gI{j})"/></g>')
            eye_front.append(doc.layer([(a, b)], front, per))
            page = ""
            x, y, w, h, snap_first, snap_idle = regions["term"]
            for _ in range(1 if strength < 3 else 2):
                sh = rng.uniform(5, 8 + 2.2 * strength)
                sy = rng.uniform(y, y + h - sh)
                cid = doc.uid("c")
                doc.defs.append(f'<clipPath id="{cid}"><rect x="{x:.1f}" y="{sy:.1f}" width="{w:.1f}" '
                                f'height="{sh:.1f}"/></clipPath>')
                sdx = rng.choice((-1, 1)) * rng.uniform(3, 4 + 3 * strength)
                page += (f'<rect x="{x:.1f}" y="{sy:.1f}" width="{w:.1f}" height="{sh:.1f}" fill="{T["bg"]}"/>'
                         f'<g clip-path="url(#{cid})"><use href="#{snap_idle if per else snap_first}" '
                         f'x="{sdx:.1f}"/></g>')
            for wx, wy, ww, wh in regions["windows"]:
                for _ in range(1 + int(strength / 2.5)):
                    ly = rng.uniform(wy + BAR + 2, wy + wh - 3)
                    page += (f'<rect x="{wx}" y="{ly:.1f}" width="{ww}" height="1.2" '
                             f'fill="{rng.choice(T["glitch"])}" opacity=".65"/>')
            for _ in range(int(1 + strength / 1.5)):
                wx, wy, ww, wh = rng.choice(regions["windows"])
                noise = "".join(rng.choice("▓▒░█▚▞#@%$&?/\\|") for _ in range(rng.randint(3, 9)))
                page += (f'<text x="{rng.uniform(wx + 4, wx + ww - 60):.1f}" '
                         f'y="{rng.uniform(wy + BAR + 12, wy + wh - 6):.1f}" '
                         f'font-size="{rng.choice((8.4, 12.2))}" fill="{rng.choice(T["glitch"] + (T["cmd"],))}">'
                         f'{esc(noise)}</text>')
            page_front.append(doc.layer([(a, b)], page, per))
            if per is None:
                shake.append((a - t0, f"transform:translate({rng.uniform(-1, 1) * (0.6 + 0.5 * strength):.2f}px,"
                                      f"{rng.uniform(-0.4, 0.4) * strength:.2f}px)"))
        if shake:
            shakes.append(doc.anim(shake, count * step, t0))
    return "".join(back), "".join(eye_front), "".join(page_front), ",".join(shakes)


def story(doc, tx, y, width, banner):
    term, statics, looks, marks = [], [], [], {}
    bcw = min(10.0, width / max(len(r) for r in banner)) if banner else 0
    brh = bcw * BANNER_ASPECT
    name = [(f"{FIRST_NAME} {LAST_NAME}", "cn"), ("  —  ", "cm"), ("hello, world", "cm")]
    links = [("github", "ca"), ("  ", None), ("linkedin", "ca"), ("  ", None), ("telegram", "ca"), (" @mvrhaa", "cm")]
    refuse = [("eye: ", "ce"), ("refusing to stop: someone is still reading this terminal", "cm")]
    session = [("cat me", ([("banner", len(banner) * brh + 10)] if banner else []) + [(name, TLH, "name")]),
               ("ls ~/links", [(links, TLH, "links")]),
               ("./eye --stop", [(refuse, TLH, "refuse")])]
    t = 0.75
    glitch_at = None
    for i, (cmd, outputs) in enumerate(session):
        if i:
            y += 7
        t_type = t + (0.55 if i == 0 else 0.35)
        markup, t_enter, (mx, my) = doc.typed(tx, y, prompt(), cmd, t, t_type)
        term.append(markup)
        statics.append((t_enter, text_el(tx, y + TLH * 0.74, prompt() + [(cmd, "cc")], TCW)))
        stop = cmd.endswith("--stop")
        looks.append((t, mx, my, 1.0, "reading the terminal"))
        if stop:
            looks.append((t_type + 0.2, mx, my, 0.55, "suspicious"))
            looks.append((t_enter, mx, my, 0.55, "stop requested"))
            glitch_at = t_enter
            t_out = t_enter + 1.5
        else:
            t_out = t_enter + 0.05
        y += TLH
        block_top, w_max, delay = y, 0.0, t_out
        for out in outputs:
            if out[0] == "banner":
                term.append(doc.banner(banner, tx, y + 4, bcw, brh, delay))
                statics.append((delay, doc.banner(banner, tx, y + 4, bcw, brh)))
                w = max(len(r) for r in banner) * bcw
                marks["banner"] = (tx + w / 2, y + out[1] / 2)
                delay += 0.04 * len(banner)
                lh = out[1]
            else:
                segs, lh, mark = out
                w = sum(len(s) for s, _ in segs) * TCW
                marks[mark] = (tx + w / 2, y + lh / 2)
                line = text_el(tx, y + lh * 0.74, segs, TCW)
                term.append(doc.appear(delay, line))
                statics.append((delay, line))
                delay += 0.035
            w_max = max(w_max, w)
            y += lh
        looks.append((t_out, tx + w_max / 2, (block_top + y) / 2, 1.0,
                      "refusing to stop" if stop else "reading the terminal"))
        t = delay + 0.5
    y += 7
    term.append(doc.appear(t, text_el(tx, y + TLH * 0.74, prompt(), TCW)
                           + f'<rect class="cur cb" x="{tx + PLEN * TCW:.1f}" y="{y + 2:.1f}" width="{TCW:.1f}" '
                             f'height="{TLH - 3:.1f}"/>'))
    looks.append((t, tx + PLEN * TCW, y + TLH / 2, 1.0, "reading the terminal"))
    return dict(term="".join(term), statics=statics, looks=looks, marks=marks, y=y + TLH, t_final=t,
                glitch_at=glitch_at)


def build(wide: bool) -> tuple[str, int]:
    doc = Doc()
    banner = banner_rows()
    margin, gap, left_w, right_w = 6, 14, 350, 484
    if wide:
        lx, ly, lw = margin, margin, left_w
        scale, gaze_scale = 1.0, (1000.0, 650.0)
        eye_h = math.ceil(BAR + 30 + EH + 16 + PAD)
        rx, ry = margin + left_w + gap, margin
    else:
        lx, ly, lw = margin, margin, right_w
        scale, gaze_scale = 1.3, (700.0, 1300.0)
        eye_h = math.ceil(BAR + 36 + (EYE_BOTTOM_ROW - EYE_TOP_ROW) * ECH * scale + 18 + PAD)
        rx, ry = margin, margin + eye_h + gap
    tx = rx + PAD
    s = story(doc, tx, ry + BAR + 10, right_w - 2 * PAD, banner)
    term_h = math.ceil(s["y"] + PAD - ry)
    if wide:
        eye_h = term_h = max(eye_h, term_h)
        W, H = margin * 2 + left_w + gap + right_w, margin * 2 + term_h
    else:
        W, H = margin * 2 + right_w, margin * 2 + eye_h + gap + term_h
    ox = lx + (lw - EW * scale) / 2
    oy = ly + BAR + 30 - (0 if wide else EYE_TOP_ROW * ECH * scale - 6)
    eye = Eye(doc, ox, oy, scale, gaze_scale)
    eye.plan(s["looks"], s["t_final"], [s["marks"].get("banner", s["marks"]["name"]), s["marks"]["name"]])

    first = "".join(m for t, m in s["statics"] if t <= s["glitch_at"] + 1e-6)
    doc.defs.append(f'<g id="tsA" class="t">{first}</g>'
                    f'<g id="tsB" class="t">{"".join(m for _, m in s["statics"])}</g>')

    windows = [(lx, ly, lw, eye_h), (rx, ry, right_w, term_h)]
    at = s["glitch_at"]
    bursts = [(at + 0.05, 3, 0.07, 2.4), (at + 0.5, 3, 0.07, 3.4), (at + 0.95, 6, 0.08, 5.0)]
    period = 3 * eye.t_loop
    base = eye.t_intro + period
    idle = (period, [(base + 5.55, 3, 0.07, 1.6), (base + eye.t_loop + 9.0, 3, 0.07, 2.8)])
    back, eye_front, page_front, shake = glitch(
        doc, eye, bursts, idle,
        {"eye": (-(lw - EW * scale) / 2 / scale, lw / scale),
         "term": (rx + 1, ry + BAR + 4, right_w - 2, term_h - BAR - 6, "tsA", "tsB"),
         "windows": windows}, random.Random(12))

    status_y = (oy + EH + 16) if wide else (oy + EYE_BOTTOM_ROW * ECH * scale + 18)
    status = (text_el(lx + PAD, status_y, [("●", "lv")], LCW)
              + text_el(lx + PAD + 2 * LCW, status_y, [("live", "cm"), (" · ", "cs")], LCW)
              + eye.label_track(lx + PAD + 9 * LCW, status_y))

    doc.defs.append(f'<radialGradient id="gG"><stop offset="0" stop-color="{T["glow"]}" stop-opacity=".22"/>'
                    f'<stop offset=".55" stop-color="{T["glow"]}" stop-opacity=".07"/>'
                    f'<stop offset="1" stop-color="{T["glow"]}" stop-opacity="0"/></radialGradient>')
    glow = (f'<ellipse cx="{eye.cx:.1f}" cy="{eye.cy:.1f}" rx="{A * eye.s * 1.15:.1f}" '
            f'ry="{HU * eye.s * 1.15:.1f}" fill="url(#gG)"/>')
    left_cmd = text_el(lx + PAD, ly + BAR + 24, prompt("~/eye") + [("./eye --ascii --watch", "cc")], LCW)
    body = [doc.window(lx, ly, lw, eye_h, f"eye — ascii — {EYE_COLS}×{EYE_ROWS}"),
            doc.window(rx, ry, right_w, term_h, f"{HANDLE}@github: ~ — zsh — 80×24"),
            glow,
            f'<g class="l">{left_cmd}</g>',
            f'<g class="t" clip-path="url(#clipT)">{s["term"]}</g>',
            eye.open() + back + f'<g class="e">{eye.frames()}{eye_front}</g></g>',
            f'<g class="l">{status}</g>',
            page_front]
    body += [doc.border(rx, ry, right_w, term_h), doc.border(lx, ly, lw, eye_h)]
    doc.defs.append(f'<clipPath id="clipT"><rect x="{rx}" y="{ry + BAR + 1}" width="{right_w}" '
                    f'height="{term_h - BAR - 1}" rx="10"/></clipPath>')

    term_colors = {"cu": T["user"], "cs": T["sym"], "ch": T["host"], "cp": T["path"], "cc": T["cmd"],
                   "cm": T["dim"], "co": T["text"], "cn": T["cmd"], "lv": T["live"], "ca": T["accent"],
                   "ce": T["accent2"]}
    ghost = T["ghost"]
    style = (f"svg{{--sc:url(#gS);--hl:{T['shine']}}}"
             f"text{{font-family:{FONT};white-space:pre;fill:{T['text']}}}"
             f".e text{{font-size:{EFS}px}}.t text{{font-size:{TFS}px}}.l text{{font-size:{LFS}px}}"
             f".wt{{font-size:12px!important;fill:{T['title']}!important;white-space:normal}}"
             ".cn{font-weight:700}.sc{fill:var(--sc)}.ir{fill:var(--ir)}.hl{fill:var(--hl)}"
             + "".join(f".{k}{{fill:{v}}}" for k, v in term_colors.items())
             + f".cb{{fill:{T['cursor']}}}"
             + f".gC{{--sc:{ghost[0][0]};--ir:{ghost[0][1]};--hl:{ghost[0][1]}}}"
             + f".gM{{--sc:{ghost[1][0]};--ir:{ghost[1][1]};--hl:{ghost[1][1]}}}"
             + f".rd{{--sc:{T['red'][0]};--ir:{T['red'][1]};--hl:{T['red'][2]}}}"
             ".fr,.h{visibility:hidden}"
             ".on{animation-name:on;animation-timing-function:step-end;animation-fill-mode:both}"
             "@keyframes on{from{visibility:hidden}to{visibility:visible}}"
             ".cw{opacity:0;animation-name:cw;animation-timing-function:step-end;animation-fill-mode:both}"
             "@keyframes cw{from{opacity:1}to{opacity:0}}"
             ".cur,.lv{animation:bl 1.1s step-end infinite}@keyframes bl{0%{opacity:1}50%{opacity:0}}"
             "@media(prefers-reduced-motion:reduce){*{animation:none!important}.fs{visibility:visible}}"
             + "".join(doc.css) + "".join(f"@keyframes {n}{{{kf}}}" for kf, n in doc.kf.items()))
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {num(W, 1)} {num(H, 1)}" width="{num(W, 1)}" '
           f'height="{num(H, 1)}" xml:space="preserve" role="img" aria-label="{html.escape(alt_text())}">'
           f'<title>{esc(FIRST_NAME)} {esc(LAST_NAME)}</title><defs>{"".join(doc.defs)}</defs><style>{style}</style>'
           f'<g style="animation:{shake}">' + "".join(body) + "</g></svg>")
    return svg, len(eye.order)


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