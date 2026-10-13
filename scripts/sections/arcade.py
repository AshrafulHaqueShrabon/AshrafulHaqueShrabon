"""Contribution game strip (abozanona/pacman-contribution-graph or Platane/snk).

The daily workflow generates the game; here its GitHub-green grid is
recolored to the accent (exact color swaps, best effort) and published for
light and dark. Until a game exists, a quiet placeholder strip is shown.
"""

from __future__ import annotations

import re

from ..style import THEMES, Doc, accent, blend
from ..svg import rect

# GitHub's contribution levels as the pacman generator writes them: empty, L1..L4.
GITHUB_LEVELS = {
    "light": ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"],
    "dark": ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"],
}


def levels(accent_name: str, theme: str) -> list[str]:
    """Empty cell + four accent shades (also passed to snk as dot colors)."""
    empty = GITHUB_LEVELS[theme][0]
    tone = accent(accent_name, theme)
    return [empty] + [blend(empty, tone, a) for a in (0.3, 0.55, 0.8, 1.0)]


def recolor(svg: str, accent_name: str, theme: str) -> str:
    mapping = dict(zip(GITHUB_LEVELS[theme][1:], levels(accent_name, theme)[1:]))
    pattern = re.compile("|".join(re.escape(k) for k in mapping), re.I)
    return pattern.sub(lambda m: mapping[m.group(0).lower()], svg)


def placeholder(theme: str) -> str:
    t = THEMES[theme]
    doc = Doc(840, 44, "Contribution game: available after the first daily update")
    return doc.render(
        rect(0.5, 0.5, 839, 43, rx=6, fill="none", stroke=t.border, stroke_dasharray="4 3")
        + f'<text class="m" x="420" y="22" dominant-baseline="central" text-anchor="middle" font-size="12" '
          f'fill="{t.muted}">the contribution game appears after the first daily update</text>')
