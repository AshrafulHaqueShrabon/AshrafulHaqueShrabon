"""Design tokens for the README images: GitHub's own fonts and colors plus
one thin accent color (amber or green).

Images use the same system font stacks as GitHub's page text, so they match
it. No fonts are embedded. Text is never width-critical: labels sit in
columns with slack, so small differences between systems don't matter.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .svg import esc, esc_attr, num

SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"
MONO_ADVANCE = 0.62  # em per character, a safe upper bound across the monospace stack


@dataclass(frozen=True)
class Theme:
    name: str
    surface: str   # button / card background
    border: str
    text: str
    muted: str
    track: str     # empty part of bars


THEMES = {
    # Values follow GitHub's own light and dark UI colors.
    "light": Theme("light", "#F6F8FA", "#D1D9E0", "#1F2328", "#59636E", "#E6EAEF"),
    "dark": Theme("dark", "#151B23", "#3D444D", "#F0F6FC", "#9198A1", "#262C36"),
}

ACCENTS = {
    "amber": {"light": "#9A6700", "dark": "#FFB000"},
    "green": {"light": "#1A7F37", "dark": "#3FB950"},
}


def accent(name: str, theme: str) -> str:
    return ACCENTS[name][theme]


def blend(color: str, other: str, amount: float) -> str:
    """Mix two #RRGGBB colors; amount=1 gives `other`."""
    a = [int(color[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(other[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * amount):02X}" for x, y in zip(a, b))


def mono_width(text: str, size: float) -> float:
    return len(text) * MONO_ADVANCE * size


@dataclass
class Doc:
    width: float
    height: float
    title: str
    css: list[str] = field(default_factory=list)

    def render(self, body: str) -> str:
        style = f".s{{font-family:{SANS}}}.m{{font-family:{MONO}}}" + "".join(self.css)
        w, h = num(self.width), num(self.height)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
                f'role="img" aria-label="{esc_attr(self.title)}"><title>{esc(self.title)}</title>'
                f"<style>{style}</style>{body}</svg>\n")
