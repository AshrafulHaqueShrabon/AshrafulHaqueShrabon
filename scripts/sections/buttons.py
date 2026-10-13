"""Link buttons: contact (Email, LinkedIn, Website) and coding profiles.

Each button is its own small image so the README can wrap it in a link
(links inside SVG images don't work). Glyphs are simple original line icons,
not brand logos.
"""

from __future__ import annotations

from ..style import THEMES, Doc, accent
from ..svg import esc, group, rect

WIDTH, HEIGHT = 156, 34

GLYPHS = {
    "email": '<rect x="1.5" y="3.5" width="13" height="9" rx="1.5"/><path d="M2 4.5l6 4.6 6-4.6"/>',
    "linkedin": ('<rect x="1.5" y="5" width="13" height="8.5" rx="1.5"/>'      # briefcase
                 '<path d="M5.5 5V3.25h5V5M1.5 9.25h13"/>'),
    "website": ('<circle cx="8" cy="8" r="6.5"/><ellipse cx="8" cy="8" rx="2.75" ry="6.5"/>'
                '<path d="M1.5 8h13"/>'),
    "code": '<path d="M5.25 4.25L1.5 8l3.75 3.75M10.75 4.25L14.5 8l-3.75 3.75M9.1 2.75L6.9 13.25"/>',
}
ARROW = '<path d="M4.5 11.5l7-7M6 4.5h5.5V10"/>'


def render(glyph: str, label: str, theme: str, accent_name: str, alt: str) -> str:
    t = THEMES[theme]
    doc = Doc(WIDTH, HEIGHT, alt)
    mid = HEIGHT / 2
    body = [
        rect(0.5, 0.5, WIDTH - 1, HEIGHT - 1, rx=6, fill=t.surface, stroke=t.border),
        group(GLYPHS[glyph], transform=f"translate(11 {mid - 8})", fill="none", stroke=accent(accent_name, theme),
              stroke_width=1.5, stroke_linecap="round", stroke_linejoin="round"),
        f'<text class="m" x="35" y="{mid}" dominant-baseline="central" font-size="13" font-weight="600" '
        f'fill="{t.text}">{esc(label)}</text>',
        group(ARROW, transform=f"translate({WIDTH - 23} {mid - 8}) scale(0.8)", fill="none", stroke=t.muted,
              stroke_width=1.6, stroke_linecap="round", stroke_linejoin="round"),
    ]
    return doc.render("".join(body))
