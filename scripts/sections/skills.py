"""Skills: one compact image, a label column plus rows of icon tiles."""

from __future__ import annotations

from .. import icons
from ..style import THEMES, Doc
from ..svg import esc

TILE, GAP = 30, 6
LABEL_W = 108
ROW_H = TILE + 8
PER_ROW = 8
FULL_NAMES = {"ml": "Machine Learning", "ai": "Artificial Intelligence"}


def names(items: list[tuple[str, str | None]]) -> list[str]:
    return [FULL_NAMES.get(icons.canonical(s), icons.label(s, o)) for s, o in items]


def alt_text(groups: list[tuple[str, list[tuple[str, str | None]]]]) -> str:
    return "Skills. " + " ".join(f"{label.title()}: {', '.join(names(items))}." for label, items in groups)


def render(groups: list[tuple[str, list[tuple[str, str | None]]]], theme: str) -> str:
    t = THEMES[theme]
    widest = max(min(len(items), PER_ROW) for _, items in groups)
    rows = sum((len(items) + PER_ROW - 1) // PER_ROW for _, items in groups)
    doc = Doc(LABEL_W + widest * (TILE + GAP) - GAP, rows * ROW_H - (ROW_H - TILE), alt_text(groups))
    body, y = [], 0.0
    for label, items in groups:
        body.append(f'<text class="m" x="0" y="{y + TILE / 2}" dominant-baseline="central" font-size="12" '
                    f'fill="{t.muted}">{esc(label.lower())}</text>')
        for start in range(0, len(items), PER_ROW):
            for i, (slug, override) in enumerate(items[start:start + PER_ROW]):
                tile = icons.embed(slug, LABEL_W + i * (TILE + GAP), y, TILE)
                name = FULL_NAMES.get(icons.canonical(slug), icons.label(slug, override))
                body.append(f"<g><title>{esc(name)}</title>{tile}</g>")
            y += ROW_H
    return doc.render("".join(body))
