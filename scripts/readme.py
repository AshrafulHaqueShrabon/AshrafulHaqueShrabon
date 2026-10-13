"""Assemble README.md and its static images from the config.

Static images (buttons, skills) live in assets/generated/ and are committed.
Dynamic images (top languages, contribution game) are published by the daily
workflow to the orphan `output` branch and embedded via raw.githubusercontent.com.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from string import Template

from . import ROOT
from .config import Config
from .readme_text import attr, html, md_text
from .sections import buttons, skills

THEMES = ("light", "dark")
GENERATED = "assets/generated"
RAW = "https://raw.githubusercontent.com/{u}/{u}/output/{name}"
BADGE_COLORS = {"amber": "9A6700", "green": "1A7F37"}  # komarev badge (white text on it)
LANGUAGES_WIDTH = 420
GAME_NAMES = {"pacman": "Pac-Man", "breakout": "Breakout", "galaga": "Galaga", "puzzle-bobble": "Puzzle Bobble",
              "bomberman": "Bomberman", "minesweeper": "Minesweeper", "snake": "Snake"}


@dataclass
class Build:
    readme: str
    static: dict[str, str] = field(default_factory=dict)   # file name → SVG
    dynamic: list[str] = field(default_factory=list)       # names expected on the output branch


def picture(light: str, dark: str, alt: str, width: str | int) -> str:
    return (f'<picture><source media="(prefers-color-scheme: dark)" srcset="{attr(dark)}">'
            f'<source media="(prefers-color-scheme: light)" srcset="{attr(light)}">'
            f'<img alt="{attr(alt)}" src="{attr(light)}" width="{width}"></picture>')


def link(href: str, inner: str) -> str:
    return f'<a href="{attr(href)}">{inner}</a>'


def label(text: str) -> str:
    """Section label: a small terminal-style prompt, the one retro nod."""
    return f"### <samp>&gt; {html(text)}</samp>"


def rows(items: list[str], most: int = 5) -> str:
    """Spread items over balanced rows (8 → 4 + 4, not 5 + 3)."""
    if not items:
        return ""
    count = math.ceil(len(items) / most)
    per_row = math.ceil(len(items) / count)
    lines = ["\n".join(items[i:i + per_row]) for i in range(0, len(items), per_row)]
    return "<p>\n" + "\n<br>\n".join(lines) + "\n</p>"


class Assembler:
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self.out = Build(readme="")

    def static_pair(self, stem: str, render) -> tuple[str, str]:
        for theme in THEMES:
            self.out.static[f"{stem}-{theme}.svg"] = render(theme)
        return tuple(f"{GENERATED}/{stem}-{theme}.svg" for theme in THEMES)

    def dynamic_pair(self, stem: str) -> tuple[str, str]:
        names = [f"{stem}-{theme}.svg" for theme in THEMES]
        self.out.dynamic += names
        return tuple(RAW.format(u=self.cfg.github_username, name=n) for n in names)

    def button(self, stem: str, glyph: str, text: str, href: str, alt: str) -> str:
        light, dark = self.static_pair(f"btn-{stem}", lambda t: buttons.render(glyph, text, t, self.cfg.accent, alt))
        return link(href, picture(light, dark, alt, buttons.WIDTH))

    # ── blocks ──
    def header(self) -> str:
        c = self.cfg
        lines = [f"# {md_text(c.display_name)}"]
        if c.headline:
            lines.append(f"<samp>{html(' | '.join(c.headline))}</samp>")
        return "\n\n".join(lines)

    def contact(self) -> str:
        c = self.cfg
        items = []
        if c.email:
            items.append(self.button("email", "email", "Email", f"mailto:{c.email}", f"Email: {c.email}"))
        if c.linkedin:
            items.append(self.button("linkedin", "linkedin", "LinkedIn", c.linkedin, "LinkedIn profile"))
        if c.website:
            items.append(self.button("website", "website", c.website_label, c.website, c.website_label))
        return rows(items)

    def bio(self) -> str:
        return md_text(self.cfg.bio) if self.cfg.bio else ""

    def profiles(self) -> str:
        items = [self.button(p.key, "code", p.label, p.url, f"{p.label} profile ({p.handle})")
                 for p in self.cfg.profiles]
        return f"{label('competitive programming')}\n\n{rows(items)}" if items else ""

    def skills(self) -> str:
        c = self.cfg
        if not c.skills:
            return ""
        light, dark = self.static_pair("skills", lambda t: skills.render(c.skills, t))
        width = re.search(r'width="([\d.]+)"', self.out.static["skills-light.svg"]).group(1)
        return f"{label('skills')}\n\n<p>{picture(light, dark, skills.alt_text(c.skills), width)}</p>"

    def languages(self) -> str:
        if not self.cfg.github_username:
            return ""
        light, dark = self.dynamic_pair("languages")
        alt = "Top languages across my public repositories (updated daily)"
        return f"{label('top languages')}\n\n<p>{picture(light, dark, alt, LANGUAGES_WIDTH)}</p>"

    def arcade(self) -> str:
        c = self.cfg
        if not c.arcade or not c.github_username:
            return ""
        light, dark = self.dynamic_pair("arcade")
        alt = f"{GAME_NAMES[c.arcade]} game played on my GitHub contribution graph (updated daily)"
        return f"<p>{picture(light, dark, alt, '100%')}</p>"

    def counter(self) -> str:
        c = self.cfg
        if not (c.visitor_counter and c.github_username):
            return ""
        src = (f"https://komarev.com/ghpvc/?username={c.github_username}&style=flat-square"
               f"&color={BADGE_COLORS[c.accent]}&label=Profile+views")
        return f'<p><img src="{attr(src)}" alt="Profile views"></p>'


def build(cfg: Config) -> Build:
    a = Assembler(cfg)
    blocks = {"header": a.header(), "contact": a.contact(), "bio": a.bio(), "profiles": a.profiles(),
              "skills": a.skills(), "languages": a.languages(), "arcade": a.arcade(), "counter": a.counter()}
    template = Template((ROOT / "templates" / "readme.md.tmpl").read_text(encoding="utf-8"))
    text = template.substitute(blocks)
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    a.out.readme = text.strip() + "\n"
    return a.out
