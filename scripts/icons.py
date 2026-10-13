"""Skill icons: slug validation, vendoring and embedding.

Brand icons come from skillicons.dev (MIT) and, for NumPy/pandas which it
lacks, from devicon (MIT). Each icon is fetched once into assets/icons/vendor/
and committed, so the README never depends on those services at view time.
Builds are offline: a missing icon renders as a placeholder until
`python build.py --fetch-icons` (or the build workflow) downloads it.

Custom tiles: "ml" (Machine Learning) and "ai" (Artificial Intelligence) are
our own art in assets/icons/custom/. On skillicons "ai" means Adobe
Illustrator; use "illustrator" here if you want that.
"""

from __future__ import annotations

import json
import re
import urllib.request
from functools import cache
from pathlib import Path

from . import ROOT

ICON_DIR = ROOT / "assets" / "icons"
VENDOR = ICON_DIR / "vendor"
CUSTOM = ICON_DIR / "custom"
REGISTRY = ICON_DIR / "registry.json"

SKILLICONS_API = "https://skillicons.dev/api/icons"
SKILLICONS_SRC = "https://raw.githubusercontent.com/tandpfun/skill-icons/main/index.js"
SKILLICONS_ICON = "https://skillicons.dev/icons?i={name}&theme=dark"
DEVICON = "https://cdn.jsdelivr.net/gh/devicons/devicon@v2.17.0/icons/{name}/{name}-original.svg"

CUSTOM_ICONS = ("ml", "ai")
DEVICON_ICONS = ("numpy", "pandas")
TILE = "#242938"  # skillicons dark tile color

LABELS = {
    "c": "C", "cpp": "C++", "cs": "C#", "python": "Python", "html": "HTML", "css": "CSS",
    "javascript": "JavaScript", "typescript": "TypeScript", "git": "Git", "github": "GitHub",
    "vscode": "VS Code", "blender": "Blender", "pytorch": "PyTorch", "tensorflow": "TensorFlow",
    "scikitlearn": "scikit-learn", "numpy": "NumPy", "pandas": "pandas", "opencv": "OpenCV",
    "ml": "ML", "ai": "AI", "linux": "Linux", "java": "Java", "golang": "Go", "rust": "Rust",
    "react": "React", "nodejs": "Node.js", "docker": "Docker", "anaconda": "Anaconda",
    "illustrator": "Illustrator", "photoshop": "Photoshop", "githubactions": "Actions",
    "markdown": "Markdown", "kotlin": "Kotlin", "matlab": "MATLAB", "r": "R", "unity": "Unity",
    "unrealengine": "Unreal", "godot": "Godot", "bash": "Bash", "vim": "Vim", "idea": "IntelliJ",
}


@cache
def registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def canonical(slug: str) -> str:
    """Map aliases (py, js, sklearn…) to the name skillicons serves."""
    slug = slug.lower()
    if slug in CUSTOM_ICONS or slug in DEVICON_ICONS:
        return slug
    return registry()["aliases"].get(slug, slug)


def check_slug(slug: str) -> str | None:
    """User-facing problem with an inventory slug, or None if it is valid."""
    if not slug:
        return "empty item"
    if not re.fullmatch(r"[a-z0-9\-]+", slug):
        return "icon IDs use lowercase letters, digits and dashes"
    if slug in CUSTOM_ICONS or slug in DEVICON_ICONS:
        return None
    if canonical(slug) in registry()["names"]:
        return None
    return "not a skillicons.dev icon ID (see the Icons List on https://skillicons.dev)"


def label(slug: str, override: str | None = None) -> str:
    if override:
        return override
    name = canonical(slug)
    return LABELS.get(name, name.replace("-", " ").title())


def path_for(slug: str) -> Path:
    name = canonical(slug)
    return (CUSTOM if name in CUSTOM_ICONS else VENDOR) / f"{name}.svg"


def available(slug: str) -> bool:
    return path_for(slug).exists()


# ── embedding ──────────────────────────────────────────────────────────────

_ROOT_RE = re.compile(r"<svg\b[^>]*>", re.S)


def namespace_ids(svg: str, prefix: str) -> str:
    """Prefix every id and #reference so icons can share one document."""
    svg = re.sub(r'\bid="([^"]+)"', lambda m: f'id="{prefix}-{m.group(1)}"', svg)
    svg = re.sub(r"url\(#([^)]+)\)", lambda m: f"url(#{prefix}-{m.group(1)})", svg)
    return re.sub(r'((?:xlink:)?href)="#([^"]+)"', lambda m: f'{m.group(1)}="#{prefix}-{m.group(2)}"', svg)


def inner_svg(markup: str) -> tuple[str, str]:
    """(viewBox, children) of the first <svg> element."""
    root = _ROOT_RE.search(markup)
    if not root:
        raise ValueError("no <svg> element")
    view = re.search(r'viewBox="([^"]+)"', root.group(0))
    width = re.search(r'\bwidth="([\d.]+)', root.group(0))
    height = re.search(r'\bheight="([\d.]+)', root.group(0))
    view_box = view.group(1) if view else f"0 0 {width.group(1) if width else 256} {height.group(1) if height else 256}"
    end = markup.rfind("</svg>")
    return view_box, markup[root.end():end]


def embed(slug: str, x: float, y: float, size: float) -> str:
    """Icon as a nested <svg> at (x, y), or a placeholder tile if not vendored."""
    from .svg import num
    path = path_for(slug)
    if not path.exists():
        return placeholder(slug, x, y, size)
    view_box, children = inner_svg(path.read_text(encoding="utf-8"))
    return (f'<svg x="{num(x)}" y="{num(y)}" width="{num(size)}" height="{num(size)}" '
            f'viewBox="{view_box}">{children}</svg>')


def placeholder(slug: str, x: float, y: float, size: float) -> str:
    from .svg import num
    r = size * 60 / 256
    return (f'<g><rect x="{num(x)}" y="{num(y)}" width="{num(size)}" height="{num(size)}" rx="{num(r)}" '
            f'fill="{TILE}"/><text x="{num(x + size / 2)}" y="{num(y + size * 0.62)}" font-size="{num(size * 0.42)}" '
            f'text-anchor="middle" fill="#8a93a6" font-family="monospace">?</text></g>')


# ── vendoring (network; used by --fetch-icons and dev tools) ───────────────

UA = {"User-Agent": "retro-profile-readme (+icon vendoring)"}


def _get(url: str) -> str:
    request = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(request, timeout=30) as resp:
        return resp.read().decode("utf-8")


def _safe(markup: str) -> None:
    lowered = markup.lower()
    if "<script" in lowered or "<foreignobject" in lowered:
        raise ValueError("icon contains scripts or foreignObject")
    refs = re.findall(r'(?:href|src)="([^"]+)"', markup)
    if any(not r.startswith("#") and not r.startswith("data:") for r in refs):
        raise ValueError("icon references external resources")


def update_registry() -> dict:
    names = json.loads(_get(SKILLICONS_API))
    source = _get(SKILLICONS_SRC)
    block = re.search(r"shortNames\s*=\s*\{(.*?)\};", source, re.S)
    aliases = dict(re.findall(r"([\w-]+)\s*:\s*'([\w-]+)'", block.group(1))) if block else {}
    data = {
        "source": "skillicons.dev/api/icons + shortNames in tandpfun/skill-icons index.js",
        "names": sorted(names),
        "aliases": dict(sorted(aliases.items())),
    }
    REGISTRY.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
    registry.cache_clear()
    return data


def fetch(slug: str) -> Path:
    """Download one icon into assets/icons/vendor/ (ids namespaced, dark tile)."""
    name = canonical(slug)
    if name in CUSTOM_ICONS:
        return path_for(slug)
    VENDOR.mkdir(parents=True, exist_ok=True)
    if name in DEVICON_ICONS:
        glyph = _get(DEVICON.format(name=name))
        _safe(glyph)
        view_box, children = inner_svg(glyph)
        tile = (f'<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256" fill="none">'
                f'<rect width="256" height="256" rx="60" fill="{TILE}"/>'
                f'<svg x="40" y="40" width="176" height="176" viewBox="{view_box}">{children}</svg></svg>')
        markup = tile
    else:
        wrapper = _get(SKILLICONS_ICON.format(name=name))
        if "undefined" in wrapper:
            raise ValueError(f"skillicons.dev has no icon '{name}'")
        _, inner = inner_svg(wrapper)
        start = inner.find("<svg")
        markup = inner[start: inner.rfind("</svg>") + 6]
    _safe(markup)
    markup = namespace_ids(markup, name)
    if 'xmlns="http://www.w3.org/2000/svg"' not in markup[:300]:
        markup = markup.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)
    out = VENDOR / f"{name}.svg"
    out.write_text(markup.strip() + "\n", encoding="utf-8")
    return out
