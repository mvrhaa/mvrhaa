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
NOTE = "Click a branch to see its repositories."
SKIP = {HANDLE.lower()}
DESCRIPTIONS = {
    "lod-qa/lodqa": "Team of 5, 1st place in the Quantum Optimization track at IBM Qiskit Fall Fest 2026. "
                    "Picks the level of detail for every 3D object under a triangle budget as a QUBO, solved with QAOA in Qiskit.",
}
ROWS = 10
SITE = f"https://{HANDLE}.github.io/"
HIDE = {"d": "(max-width: 700px)", "m": "(min-width: 701px)"}

ROOT = pathlib.Path(__file__).resolve().parent
OUT_DIR = ROOT / "assets"
DATA = ROOT / "data" / "repos.json"
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
FACES = {"regular": ("Figtree-Regular.ttf", 400), "semibold": ("Figtree-SemiBold.ttf", 600)}
FAMILY = "rm-figtree"
STACK = f"{FAMILY},'Avenir Next','Segoe UI',Helvetica,Arial,sans-serif"
BLANK = '<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="1" viewBox="0 0 1000 1"/>'


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


def pinned() -> list[str]:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN is needed to read the pinned repositories")
    query = ('{ user(login: "%s") { pinnedItems(first: 6, types: REPOSITORY) '
             '{ nodes { ... on Repository { nameWithOwner isPrivate } } } } }' % HANDLE)
    request = urllib.request.Request(
        "https://api.github.com/graphql", data=json.dumps({"query": query}).encode("utf-8"),
        headers={"Authorization": f"Bearer {token}", "User-Agent": "profile-readme-generator",
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    if data.get("errors"):
        raise SystemExit(f"GitHub GraphQL error: {data['errors']}")
    return [n["nameWithOwner"] for n in data["data"]["user"]["pinnedItems"]["nodes"] if not n["isPrivate"]]


def fetch_repos() -> list[dict]:
    items = [r for r in api(f"/users/{HANDLE}/repos?type=owner&per_page=100")
             if not (r["fork"] or r["archived"] or r["private"] or r["name"].lower() in SKIP)]
    for full in pinned():
        r = api(f"/repos/{full}")
        if not r["private"] and r["name"].lower() not in SKIP and all(i["full_name"] != r["full_name"] for i in items):
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
    return lines[:max_lines]


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
        self.css: str | None = None

    def add(self, part: str) -> None:
        self.parts.append(part)

    def text(self, x: float, y: float, s: str, size: float, fill: str, face: str = "regular",
             anchor: str = "start", tnum: bool = False) -> None:
        self.used[face].update(s)
        style = ' style="font-feature-settings:\'tnum\'"' if tnum else ""
        self.parts.append(
            f'<text x="{num(x)}" y="{num(y)}" font-size="{num(size)}" font-weight="{FACES[face][1]}" '
            f'fill="{fill}" text-anchor="{anchor}"{style}>{html.escape(s, quote=False)}</text>')

    def render(self, w: float, h: float, x0: float = 0.0, x1: float | None = None) -> str:
        if self.css is None:
            self.css = "".join(font_face(face, chars) for face, chars in self.used.items() if chars)
        x1 = w if x1 is None else x1
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{num(x1 - x0)}" height="{num(h)}" '
                f'viewBox="{num(x0)} 0 {num(x1 - x0)} {num(h)}" font-family="{STACK}">'
                f'<style>{self.css}</style>'
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
        if r["lang"] and r["lang"] not in order:
            order.append(r["lang"])
    return order


def earlier(rest: list[dict]) -> dict:
    return dict(name=f"{len(rest)} earlier", date="", lang=None, about="")


def capped(repos: list[dict]) -> list[dict]:
    return repos[:ROWS] + ([earlier(repos[ROWS:])] if len(repos) > ROWS else [])


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
             trunk_x: float, step: float, top: float, bottom: float) -> dict[str, float]:
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
    return xs


def wide(repos: list[dict]):
    W, P = 880, 32
    c = Canvas()
    colors = colors_for(repos)
    rows = capped(repos)
    order = lanes(rows)
    step = min(24.0, 168 / max(len(order), 1))
    room = W - P - (292 + step * len(order) + 40 + width("0000-00-00", "regular", 12) + 28)
    blocks = [wrap(r["about"], "regular", 13, room, 2) for r in rows]
    trunk_x = round(W / 2 - step * len(order) / 2, 1)

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
    c.text(P, H - P, NOTE, 12, DIM)
    xs = branches(c, rows, ys, colors, order, trunk_x, step, P - 14, H - 14)
    return c, W, H, [xs[lang] for lang in order], step, order


def narrow(repos: list[dict]):
    W, P = 440, 22
    c = Canvas()
    colors = colors_for(repos)
    rows = capped(repos)
    order = lanes(rows)
    step = min(28.0, 140 / max(len(order), 1))
    room = W - P - (P + 6 + step * len(order) + 22)
    blocks = [wrap(r["about"], "regular", 13, room, 3) for r in rows]
    trunk_x = round(W / 2 - step * len(order) / 2, 1)

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
    H = bottom + 40 + P
    c.text(P, H - P, NOTE, 12, DIM)
    xs = branches(c, rows, ys, colors, order, trunk_x, step, top, H - 46)
    return c, W, H, [xs[lang] for lang in order], step, order


def strips(c: Canvas, W: float, H: float, xs: list[float], step: float) -> list[tuple[str, float]]:
    cuts = [round(x - step / 2, 1) for x in xs] + ([round(xs[-1] + step / 2, 1)] if xs else [])
    bounds = [0.0] + cuts + [float(W)]
    return [(c.render(W, H, x0, x1), (x1 - x0) / W * 99.8) for x0, x1 in zip(bounds, bounds[1:])]


def slug(lang: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", lang.lower().replace("+", "p").replace("#", "sharp")).strip("-")


def build(repos: list[dict]):
    files = {"blank.svg": BLANK}
    cuts: dict[str, list[tuple[str, float]]] = {}
    order: list[str] = []
    for kind, draw in (("d", wide), ("m", narrow)):
        c, W, H, xs, step, order = draw(repos)
        cuts[kind] = []
        for i, (svg, pct) in enumerate(strips(c, W, H, xs, step)):
            files[f"{kind}-{i}.svg"] = svg
            cuts[kind].append((f"{kind}-{i}.svg", pct))
    return order, files, cuts


def image_url(file: str, svg: str) -> str:
    version = hashlib.sha256(svg.encode("utf-8")).hexdigest()[:10]
    return f"https://raw.githubusercontent.com/{HANDLE}/{HANDLE}/main/assets/{file}?v={version}"


def alt_text(repos: list[dict]) -> str:
    stack = ", ".join(f"{lang} {n}" for lang, n in counts(repos))
    return (f"{NAME} ({HANDLE}), {', '.join(ABOUT)}. Branch graph of public repositories, "
            f"one branch per language: {stack}. Each branch opens its repositories.")


def targets(repos: list[dict], order: list[str]) -> list[tuple[str, str]]:
    lanes_ = [(f"{SITE}#{slug(lang)}", f"{lang} branch: open its repositories") for lang in order]
    return [(SITE, alt_text(repos))] + lanes_ + ([(SITE, "")] if order else [])


def strip_row(kind: str, cuts, urls: dict[str, str], links: list[tuple[str, str]]) -> str:
    parts = []
    for (name, pct), (link, alt) in zip(cuts[kind], links):
        parts.append(f'<a href="{link}"><picture><source media="{HIDE[kind]}" srcset="{urls["blank.svg"]}">'
                     f'<img src="{urls[name]}" width="{pct:.3f}%" alt="{html.escape(alt)}"></picture></a>')
    return "<p>" + "".join(parts) + "</p>"


def readme(repos: list[dict], order, cuts, urls: dict[str, str]) -> str:
    links = targets(repos, order)
    contacts = "&nbsp;&nbsp;\n  ".join(f'<a href="{url}"><code>{html.escape(label)}</code></a>'
                                       for label, url in LINKS)
    bio = BIO.read_text(encoding="utf-8").strip() + "\n\n" if BIO.exists() else ""
    return f"""{strip_row("d", cuts, urls, links)}
{strip_row("m", cuts, urls, links)}

{bio}<p>
  <code>~/links</code>&nbsp;&nbsp;
  {contacts}
</p>
"""


def site_data(repos: list[dict]) -> str:
    data = dict(name=NAME, handle=HANDLE, about=list(ABOUT),
                links=[dict(label=label, url=url) for label, url in LINKS],
                colors=colors_for(repos),
                repos=[dict(name=r["name"], url=r["url"], lang=r["lang"], date=r["date"], about=r["about"])
                       for r in repos])
    return json.dumps(data, ensure_ascii=False, indent=1) + "\n"


if __name__ == "__main__":
    repos = fetch_repos()
    order, files, cuts = build(repos)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUT_DIR.glob("*.svg"):
        if old.name not in files:
            old.unlink()
    urls = {}
    for name, svg in files.items():
        (OUT_DIR / name).write_text(svg, encoding="utf-8")
        urls[name] = image_url(name, svg)
    DATA.parent.mkdir(parents=True, exist_ok=True)
    DATA.write_text(site_data(repos), encoding="utf-8")
    README.write_text(readme(repos, order, cuts, urls), encoding="utf-8")
    size = sum(len(s.encode()) for s in files.values()) / 1024
    print(f"assets: {len(files)} files, {size:.0f} KB; data: {len(repos)} repositories")
