"""Top languages: one stacked bar in GitHub's own language colors, plus a legend.

Data comes from the daily workflow (owned, non-fork repositories). Until the
first successful fetch, a quiet placeholder is shown instead.
"""

from __future__ import annotations

from ..style import THEMES, Doc, mono_width
from ..svg import el, esc, rect

WIDTH = 420
BAR_H = 8
COLS = 3
ROW_H = 20


def shares(languages: list[list], top: int, exclude: list[str]) -> list[tuple[str, float, str | None]]:
    """[(name, share, color)] for the top languages, plus "Other" for the rest."""
    skip = {e.lower() for e in exclude}
    langs = []
    for entry in languages:  # [name, bytes, color] as cached by the live job
        name, size = entry[0], entry[1]
        color = entry[2] if len(entry) > 2 else None
        if name.lower() not in skip and size > 0:
            langs.append((name, size, color))
    total = sum(size for _, size, _ in langs)
    if not total:
        return []
    out = [(name, size / total, color) for name, size, color in langs[:top]]
    rest = 1 - sum(share for _, share, _ in out)
    if rest >= 0.005:
        out.append(("Other", rest, None))
    return out


def alt_text(items: list[tuple[str, float, str | None]]) -> str:
    return "Top languages: " + ", ".join(f"{name} {share * 100:.1f}%" for name, share, _ in items)


def render(items: list[tuple[str, float, str | None]], theme: str) -> str:
    t = THEMES[theme]
    if not items:
        doc = Doc(WIDTH, 40, "Top languages: available after the first daily update")
        return doc.render(
            rect(0.5, 0.5, WIDTH - 1, 39, rx=6, fill="none", stroke=t.border, stroke_dasharray="4 3")
            + f'<text class="m" x="{WIDTH / 2}" y="20" dominant-baseline="central" text-anchor="middle" '
              f'font-size="12" fill="{t.muted}">top languages appear after the first daily update</text>')
    rows = (len(items) + COLS - 1) // COLS
    doc = Doc(WIDTH, BAR_H + 12 + rows * ROW_H - 6, alt_text(items))
    clip = el("clipPath", {"id": "bar"}, rect(0, 0, WIDTH, BAR_H, rx=BAR_H / 2))
    segments, x = [], 0.0
    for i, (_, share, color) in enumerate(items):
        w = WIDTH - x if i == len(items) - 1 else max(share * WIDTH, 2)
        segments.append(rect(round(x, 2), 0, round(w, 2), BAR_H, fill=color or t.muted))
        x += w
    body = [f"<defs>{clip}</defs>", rect(0, 0, WIDTH, BAR_H, rx=BAR_H / 2, fill=t.track),
            f'<g clip-path="url(#bar)">{"".join(segments)}</g>']
    col_w = WIDTH / COLS
    for i, (name, share, color) in enumerate(items):
        cx, cy = (i % COLS) * col_w, BAR_H + 12 + (i // COLS) * ROW_H + 6
        pct = f"{share * 100:.1f}%"
        fits = int((col_w - 18) / mono_width("x", 12))  # characters per legend column
        shown = name if len(name) + 1 + len(pct) <= fits else name[: max(1, fits - len(pct) - 2)] + "…"
        body.append(el("circle", {"cx": cx + 4, "cy": cy, "r": 4, "fill": color or t.muted}))
        body.append(f'<text class="m" x="{cx + 14}" y="{cy}" dominant-baseline="central" font-size="12" '
                    f'fill="{t.text}">{esc(shown)} <tspan fill="{t.muted}">{pct}</tspan></text>')
    return doc.render("".join(body))
