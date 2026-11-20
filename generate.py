from __future__ import annotations

import base64
import collections
import functools
import hashlib
import html
import io
import json
import os
import pathlib
import re
import urllib.error
import urllib.request

from fontTools import subset
from fontTools.ttLib import TTFont

NAME = "Ruslan Murha"
HANDLE = "mvrhaa"
ABOUT = ("Security, DevOps and cloud", "CS student at PJATK, Warsaw")
LINKS = (
    ("linkedin", "https://www.linkedin.com/in/ruslan-murha-08309638a"),
    ("telegram @mvrhaa", "https://t.me/mvrhaa"),
)
NOTE = "Public repositories, updated automatically."
SKIP = {HANDLE.lower()}
EXTRA = ("lod-qa/lodqa",)
DESCRIPTIONS = {
    "lod-qa/lodqa": "Team of 5, 1st place in the Quantum Optimization track at IBM Qiskit Fall Fest 2026. "
                    "Picks the level of detail for every 3D object under a triangle budget as a QUBO, solved with QAOA in Qiskit.",
}
ROWS_WIDE = 10
ROWS_NARROW = 8

ROOT = pathlib.Path(__file__).resolve().parent
OUT_DIR = ROOT / "assets"
README = ROOT / "README.md"
BIO = ROOT / "bio.md"
FONTS = ROOT / "fonts"

BG, EDGE, INK, BODY, DIM, TRUNK = "#0d1117", "#30363d", "#e6edf3", "#9198a1", "#6e7681", "#3d444d"
LANG_COLORS = {
    "Python": "#6cb6ff", "Java": "#f0883e", "TypeScript": "#b083f0", "JavaScript": "#e3b341",
    "Swift": "#f47067", "Go": "#39c5cf", "Rust": "#dea584", "C++": "#f778ba", "C": "#8ddb8c",
    "C#": "#57ab5a", "Kotlin": "#d2a8ff", "Shell": "#a5d6ff", "HTML": "#ff938a",
}
SPARE = ("#56d364", "#ffa198", "#79c0ff", "#e2c541", "#bc8cff", "#ff9bce")
OTHER = "#8b949e"
DOTS = {
    "#6cb6ff": "🔵", "#f0883e": "🟠", "#b083f0": "🟣", "#e3b341": "🟡", "#f47067": "🔴", "#39c5cf": "🔵",
    "#dea584": "🟤", "#f778ba": "🔴", "#8ddb8c": "🟢", "#57ab5a": "🟢", "#d2a8ff": "🟣", "#a5d6ff": "🔵",
    "#ff938a": "🔴", "#56d364": "🟢", "#ffa198": "🔴", "#79c0ff": "🔵", "#e2c541": "🟡", "#bc8cff": "🟣",
    "#ff9bce": "🔴", OTHER: "⚪",
}
FACES = {"regular": ("Figtree-Regular.ttf", 400), "semibold": ("Figtree-SemiBold.ttf", 600)}
FAMILY = "rm-figtree"
STACK = f"{FAMILY},'Avenir Next','Segoe UI',Helvetica,Arial,sans-serif"


def api(path: str, raw: bool = False):
    headers = {
        "Accept": "application/vnd.github.raw" if raw else "application/vnd.github+json",
        "User-Agent": "profile-readme-generator",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request("https://api.github.com" + path, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read().decode("utf-8")
    return body if raw else json.loads(body)


def plain(text: str) -> str:
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
    return re.sub(r"[`*]", "", text).strip()


def first_sentence(markdown: str) -> str:
    lines = [line.strip() for line in markdown.splitlines()]
    para: list[str] = []
    i = 0
    while i < len(lines):
        s = lines[i]
        i += 1
        if s and set(s) <= set("=-"):
            para = []
            continue
        if not s or s.startswith(("#", "!", "<", ">", "|", "```", "[!", "- ", "* ")):
            if para:
                break
            continue
        para.append(s)
    text = plain(" ".join(para))
    if text.endswith(":"):
        items: list[str] = []
        for s in lines[i:]:
            if s.startswith(("- ", "* ")):
                items.append(plain(s[2:]))
            elif s or items:
                break
        if items:
            return f"{text} {', '.join(items)}"
    m = re.match(r"(.+?[.!?])(\s|$)", text)
    return (m.group(1) if m else text).strip()


def readme_line(full_name: str) -> str:
    try:
        return first_sentence(api(f"/repos/{full_name}/readme", raw=True))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return ""
        raise


def entry(r: dict) -> dict:
    full = r["full_name"]
    about = DESCRIPTIONS.get(full) or (r["description"] or "").strip() or readme_line(full)
    own = r["owner"]["login"].lower() == HANDLE.lower()
    return dict(name=r["name"] if own else full, url=r["html_url"], lang=r["language"] or "Other",
                date=r["created_at"][:10], about=about)


def fetch_repos() -> list[dict]:
    items = [r for r in api(f"/users/{HANDLE}/repos?type=owner&per_page=100")
             if not (r["fork"] or r["archived"] or r["private"] or r["name"].lower() in SKIP)]
    for full in EXTRA:
        r = api(f"/repos/{full}")
        if not r["private"] and all(i["full_name"] != r["full_name"] for i in items):
            items.append(r)
    return sorted((entry(r) for r in items), key=lambda r: (r["date"], r["name"]), reverse=True)


@functools.lru_cache(maxsize=None)
def metrics(face: str):
    font = TTFont(FONTS / FACES[face][0])
    return font.getBestCmap(), font["hmtx"].metrics, font["head"].unitsPerEm


def width(s: str, face: str, size: float) -> float:
    cmap, hmtx, upm = metrics(face)
    fallback = hmtx[cmap[ord("n")]][0]
    return sum(hmtx[cmap[ord(c)]][0] if ord(c) in cmap else fallback for c in s) * size / upm


def wrap(text: str, face: str, size: float, room: float, max_lines: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        trial = f"{current} {word}".strip()
        if not current or width(trial, face, size) <= room:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    cut = len(lines) > max_lines
    lines = lines[:max_lines]
    return [fit(line, face, size, room, cut and i == len(lines) - 1) for i, line in enumerate(lines)]


def fit(line: str, face: str, size: float, room: float, cut: bool) -> str:
    while line and width(line + ("…" if cut else ""), face, size) > room:
        line, cut = line[:-1].rstrip(), True
    return line.rstrip(" ,.;:-") + "…" if cut else line


def font_face(face: str, chars: set[str]) -> str:
    font = TTFont(FONTS / FACES[face][0], recalcTimestamp=False)
    options = subset.Options()
    options.flavor = "woff2"
    options.layout_features = ["kern", "tnum"]
    subsetter = subset.Subsetter(options)
    subsetter.populate(text="".join(sorted(chars)))
    subsetter.subset(font)
    font.flavor = "woff2"
    buffer = io.BytesIO()
    font.save(buffer)
    data = base64.b64encode(buffer.getvalue()).decode("ascii")
    return (f"@font-face{{font-family:{FAMILY};font-weight:{FACES[face][1]};"
            f"src:url(data:font/woff2;base64,{data}) format('woff2')}}")


def num(v: float) -> str:
    return f"{v:.1f}".rstrip("0").rstrip(".")


class Canvas:
    def __init__(self) -> None:
        self.parts: list[str] = []
        self.used: dict[str, set[str]] = {face: set() for face in FACES}

    def add(self, part: str) -> None:
        self.parts.append(part)

    def text(self, x: float, y: float, s: str, size: float, fill: str, face: str = "regular",
             anchor: str = "start", tnum: bool = False) -> None:
        self.used[face].update(s)
        style = ' style="font-feature-settings:\'tnum\'"' if tnum else ""
        self.parts.append(
            f'<text x="{num(x)}" y="{num(y)}" font-size="{num(size)}" font-weight="{FACES[face][1]}" '
            f'fill="{fill}" text-anchor="{anchor}"{style}>{html.escape(s, quote=False)}</text>')

    def render(self, w: float, h: float) -> str:
        css = "".join(font_face(face, chars) for face, chars in self.used.items() if chars)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{num(w)}" height="{num(h)}" '
                f'viewBox="0 0 {num(w)} {num(h)}" font-family="{STACK}">'
                f'<style>{css}</style>'
                f'<rect x=".5" y=".5" width="{num(w - 1)}" height="{num(h - 1)}" rx="10" '
                f'fill="{BG}" stroke="{EDGE}"/>' + "".join(self.parts) + "</svg>")


def colors_for(repos: list[dict]) -> dict[str, str]:
    spare = iter(SPARE * 8)
    colors = {}
    for r in reversed(repos):
        lang = r["lang"]
        if lang not in colors:
            colors[lang] = OTHER if lang == "Other" else LANG_COLORS.get(lang) or next(spare)
    return colors


def counts(repos: list[dict]) -> list[tuple[str, int]]:
    return sorted(collections.Counter(r["lang"] for r in repos).items(), key=lambda kv: (-kv[1], kv[0]))


def legend(repos: list[dict], rows: list[dict]) -> list[tuple[str, int]]:
    shown = {r["lang"] for r in rows if r["lang"]}
    return [(lang, n) for lang, n in counts(repos) if lang in shown]


def lanes(rows: list[dict]) -> list[str]:
    order: list[str] = []
    for r in reversed(rows):
        if r["lang"] not in order:
            order.append(r["lang"])
    return order


def earlier(rest: list[dict]) -> dict:
    first, last = rest[-1]["date"][:7], rest[0]["date"][:7]
    span = first if first == last else f"{first} – {last}"
    noun = "repository" if len(rest) == 1 else "repositories"
    return dict(name=f"{len(rest)} earlier {noun}", date="", lang=None,
                about=f"{span}: " + ", ".join(r["name"] for r in rest))


def capped(repos: list[dict], limit: int) -> list[dict]:
    return repos[:limit] + ([earlier(repos[limit:])] if len(repos) > limit else [])


def row_height(lines: list[str]) -> float:
    return 24 + 18 * (len(lines) - 1) if lines else 8


def place(blocks: list[list[str]], start: float, fill_to: float) -> tuple[list[float], float]:
    ys, y = [], start
    for lines in blocks:
        ys.append(y)
        y += row_height(lines) + 24
    bottom = ys[-1] + row_height(blocks[-1]) if ys else start
    if len(ys) > 1 and bottom < fill_to:
        gap = min(16.0, (fill_to - bottom) / (len(ys) - 1))
        ys = [y + gap * i for i, y in enumerate(ys)]
        bottom += gap * (len(ys) - 1)
    return ys, bottom


def branches(c: Canvas, rows: list[dict], ys: list[float], colors: dict[str, str], order: list[str],
             trunk_x: float, step: float, top: float, bottom: float) -> None:
    xs = {lang: trunk_x + step * (i + 1) for i, lang in enumerate(order)}
    if ys:
        bottom = max(bottom, ys[-1] + 40)
    c.add(f'<defs><linearGradient id="fade" gradientUnits="userSpaceOnUse" x1="0" y1="{num(top)}" '
          f'x2="0" y2="{num(bottom)}"><stop offset=".7" stop-color="{TRUNK}"/>'
          f'<stop offset="1" stop-color="{TRUNK}" stop-opacity="0"/></linearGradient></defs>')
    c.add(f'<path d="M{num(trunk_x)} {num(top)}V{num(bottom)}" stroke="url(#fade)" stroke-width="2.5" '
          f'fill="none"/>')
    oldest = {}
    for r, y in zip(rows, ys):
        if r["lang"]:
            oldest[r["lang"]] = y
    for lang, y in oldest.items():
        x = xs[lang]
        c.add(f'<path d="M{num(trunk_x)} {num(y + 30)}C{num(trunk_x)} {num(y + 14)} {num(x)} {num(y + 18)} '
              f'{num(x)} {num(y)}V{num(top)}" stroke="{colors[lang]}" stroke-width="2.5" fill="none" '
              f'stroke-linecap="round"/>')
    for r, y in zip(rows, ys):
        x, fill = (xs[r["lang"]], colors[r["lang"]]) if r["lang"] else (trunk_x, TRUNK)
        c.add(f'<circle cx="{num(x)}" cy="{num(y)}" r="5.5" fill="{fill}" stroke="{BG}" stroke-width="3"/>')


def repo_count(repos: list[dict], lang: str) -> str:
    n = sum(1 for r in repos if r["lang"] == lang)
    return f"{n} public {'repository' if n == 1 else 'repositories'}"


def wide(repos: list[dict], focus: str | None = None) -> str:
    W, P = 880, 32
    c = Canvas()
    colors = colors_for(repos)
    rows = capped(repos, ROWS_WIDE)
    order = lanes([r for r in rows if r["lang"]])
    trunk_x = 292
    step = min(24.0, 168 / max(len(order), 1))
    date_x = trunk_x + step * len(order) + 40
    name_x = date_x + width("0000-00-00", "regular", 12) + 28
    room = W - P - name_x

    if focus:
        rows = capped([r for r in repos if r["lang"] == focus], ROWS_WIDE)
        blocks = [wrap(r["about"], "regular", 13, room, 2) for r in rows]
        c.text(P, P + 26, focus, 28, colors[focus], "semibold")
        c.text(P, P + 56, repo_count(repos, focus), 15, BODY)
        left_bottom = P + 56
    else:
        blocks = [[""] for _ in rows]
        c.text(P, P + 26, NAME, 28, INK, "semibold")
        for i, line in enumerate(ABOUT):
            c.text(P, P + 56 + 21 * i, line, 15, BODY)
        ly = P + 128
        for lang, n in legend(repos, rows):
            c.add(f'<circle cx="{P + 6}" cy="{ly - 5}" r="5" fill="{colors[lang]}"/>')
            c.text(P + 22, ly, lang, 14, INK)
            c.text(P + 228, ly, str(n), 13, DIM, anchor="end", tnum=True)
            ly += 28
        left_bottom = ly + 22

    ys, bottom = place(blocks, P + 12, left_bottom - 14)
    H = max(left_bottom, bottom) + P
    if not focus:
        c.text(P, H - P, NOTE, 12, DIM)
    branches(c, rows, ys, colors, order, trunk_x, step, P - 14, H - 14)
    if focus:
        for r, y, lines in zip(rows, ys, blocks):
            if r["date"]:
                c.text(date_x, y + 4, r["date"], 12, DIM, tnum=True)
            c.text(name_x, y + 5, r["name"], 15, INK if r["lang"] else BODY, "semibold")
            for k, line in enumerate(lines):
                c.text(name_x, y + 24 + 18 * k, line, 13, BODY)
    return c.render(W, H)


def narrow(repos: list[dict], focus: str | None = None) -> str:
    W, P = 440, 22
    c = Canvas()
    colors = colors_for(repos)
    rows = capped(repos, ROWS_NARROW)
    order = lanes([r for r in rows if r["lang"]])
    trunk_x = P + 6
    step = min(16.0, 112 / max(len(order), 1))
    text_x = trunk_x + step * len(order) + 22
    room = W - P - text_x

    if focus:
        rows = capped([r for r in repos if r["lang"] == focus], ROWS_NARROW)
        blocks = [wrap(r["about"], "regular", 13, room, 3) for r in rows]
        c.text(P, P + 22, focus, 24, colors[focus], "semibold")
        y = P + 48
        c.text(P, y, repo_count(repos, focus), 15, BODY)
    else:
        blocks = [[""] for _ in rows]
        c.text(P, P + 22, NAME, 24, INK, "semibold")
        y = P + 50
        for about in ABOUT:
            for line in wrap(about, "regular", 15, W - 2 * P, 2):
                c.text(P, y, line, 15, BODY)
                y += 20
        x, y = P, y + 16
        for lang, n in legend(repos, rows):
            item = 14 + width(lang, "regular", 13) + 6 + width(str(n), "regular", 13)
            if x > P and x + item > W - P:
                x, y = P, y + 22
            c.add(f'<circle cx="{num(x + 4.5)}" cy="{num(y - 4.5)}" r="4.5" fill="{colors[lang]}"/>')
            c.text(x + 14, y, lang, 13, INK)
            c.text(x + 14 + width(lang, "regular", 13) + 6, y, str(n), 13, DIM, tnum=True)
            x += item + 18

    top = y + 22
    ys, bottom = place(blocks, top + 18, 0)
    if focus:
        H = bottom + 24 + P
        branches(c, rows, ys, colors, order, trunk_x, step, top, H - 14)
    else:
        H = bottom + 40 + P
        c.text(P, H - P, NOTE, 12, DIM)
        branches(c, rows, ys, colors, order, trunk_x, step, top, H - 46)
    if focus:
        for r, y, lines in zip(rows, ys, blocks):
            c.text(text_x, y + 5, r["name"], 15, INK if r["lang"] else BODY, "semibold")
            if r["date"] and width(r["name"], "semibold", 15) + width(r["date"], "regular", 12) + 12 <= room:
                c.text(W - P, y + 5, r["date"], 12, DIM, anchor="end", tnum=True)
            for k, line in enumerate(lines):
                c.text(text_x, y + 24 + 18 * k, line, 13, BODY)
    return c.render(W, H)


def slug(lang: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", lang.lower().replace("+", "p").replace("#", "sharp")).strip("-")


def images(repos: list[dict]) -> dict[str, str]:
    files = {"graph.svg": wide(repos), "graph-mobile.svg": narrow(repos)}
    for lang, _ in counts(repos):
        files[f"branch-{slug(lang)}.svg"] = wide(repos, lang)
        files[f"branch-{slug(lang)}-mobile.svg"] = narrow(repos, lang)
    return files


def image_url(file: str, svg: str) -> str:
    version = hashlib.sha256(svg.encode("utf-8")).hexdigest()[:10]
    return f"https://raw.githubusercontent.com/{HANDLE}/{HANDLE}/main/assets/{file}?v={version}"


def picture(urls: dict[str, str], name: str, alt: str) -> str:
    return (f'<picture>\n  <source media="(max-width: 700px)" srcset="{urls[name + "-mobile.svg"]}">\n'
            f'  <img src="{urls[name + ".svg"]}" width="100%" alt="{html.escape(alt)}">\n</picture>')


def alt_text(repos: list[dict]) -> str:
    stack = ", ".join(f"{lang} {n}" for lang, n in counts(repos))
    return (f"{NAME} ({HANDLE}), {', '.join(ABOUT)}. "
            f"Branch graph of public repositories, one branch per language: {stack}.")


def branch_sections(repos: list[dict], urls: dict[str, str]) -> str:
    colors = colors_for(repos)
    sections = []
    for lang, n in counts(repos):
        items = [r for r in repos if r["lang"] == lang]
        alt = f"{lang} branch: " + "; ".join(f"{r['name']} ({r['date']}): {r['about']}" for r in items)
        links = "&nbsp;&nbsp;\n  ".join(f'<a href="{r["url"]}"><code>{html.escape(r["name"])}</code></a>'
                                        for r in items)
        noun = "repository" if n == 1 else "repositories"
        sections.append(
            f"<details>\n<summary>{DOTS.get(colors[lang], '⚪')} <b>{html.escape(lang)}</b> &nbsp;{n} {noun}"
            f"</summary>\n<br>\n\n{picture(urls, f'branch-{slug(lang)}', alt)}\n\n<p>\n  {links}\n</p>\n\n</details>")
    return "\n".join(sections)


def readme(repos: list[dict], urls: dict[str, str]) -> str:
    contacts = "&nbsp;&nbsp;\n  ".join(f'<a href="{url}"><code>{html.escape(label)}</code></a>'
                                       for label, url in LINKS)
    bio = BIO.read_text(encoding="utf-8").strip() + "\n\n" if BIO.exists() else ""
    return f"""{picture(urls, "graph", alt_text(repos))}

{branch_sections(repos, urls)}

{bio}<p>
  <code>~/links</code>&nbsp;&nbsp;
  {contacts}
</p>
"""


if __name__ == "__main__":
    repos = fetch_repos()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    files = images(repos)
    for old in OUT_DIR.glob("branch-*.svg"):
        if old.name not in files:
            old.unlink()
    urls = {}
    for file, svg in files.items():
        (OUT_DIR / file).write_text(svg, encoding="utf-8")
        urls[file] = image_url(file, svg)
        print(f"{file}: {len(svg.encode()) / 1024:.0f} KB")
    README.write_text(readme(repos, urls), encoding="utf-8")
    print(f"README.md: {len(repos)} repositories")
